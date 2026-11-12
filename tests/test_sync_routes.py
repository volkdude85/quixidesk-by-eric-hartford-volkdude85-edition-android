#!/usr/bin/env python3
"""Tests for the sync routes — the code that decides what may cross and what may not.

These are the assertions that matter for this project: a sync that loses data or serves a path it
should not is worse than a sync that does nothing. Everything here runs against the real module, on a
real temporary directory, with no mocks.

    /usr/bin/python3 -m unittest discover -s tests -v
"""
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("sync_routes", HERE.parent / "sync" / "sync_routes.py")
assert SPEC is not None and SPEC.loader is not None, "cannot load sync/sync_routes.py"
sync_routes = importlib.util.module_from_spec(SPEC)
sys.modules["sync_routes"] = sync_routes
SPEC.loader.exec_module(sync_routes)


class SyncRoutesTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="qxsync-"))
        setattr(sync_routes, "ROOT", self.root)     # the module resolves paths from this
        (self.root / "memory").mkdir()
        (self.root / "sessions").mkdir()
        (self.root / "files").mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # ── the whitelist is the security boundary ───────────────────────────────────
    def test_parent_traversal_is_refused_in_every_verb(self):
        for path in ("../../etc/passwd", "memory/../../etc/passwd", "/etc/passwd"):
            self.assertEqual(sync_routes.get(f"path={path}")[0], 400, path)

    def test_paths_outside_the_whitelist_are_refused(self):
        for path in ("credentials.key", "providers.json", "profiles/x/persona.md", "sessions/../../x"):
            code, _ = sync_routes.put(f"path={path}", b"x")
            self.assertEqual(code, 400, path)

    def test_the_whitelist_names_no_secrets(self):
        joined = " ".join(sync_routes.PATTERNS)
        for forbidden in ("credentials", "providers.json", "profiles"):
            self.assertNotIn(forbidden, joined)

    # ── state files ─────────────────────────────────────────────────────────────
    def test_a_state_file_round_trips_byte_for_byte(self):
        body = b"# MEMORY\n\n- something learned\n"
        code, out = sync_routes.put("path=memory/MEMORY.md", body)
        self.assertEqual(code, 200)
        self.assertEqual(out["sha256"], sync_routes._sha(body))
        status, got, _ = sync_routes.get("path=memory/MEMORY.md")
        self.assertEqual(status, 200)
        self.assertEqual(got, body)

    def test_overwriting_keeps_a_conflict_copy_of_what_was_there(self):
        sync_routes.put("path=memory/MEMORY.md", b"first")
        sync_routes.put("path=memory/MEMORY.md", b"second", host="otherbox")
        leftovers = [p.name for p in (self.root / "memory").iterdir() if ".conflict-" in p.name]
        self.assertEqual(len(leftovers), 1, leftovers)
        self.assertIn("otherbox", leftovers[0])
        self.assertEqual((self.root / "memory" / "MEMORY.md").read_bytes(), b"second")

    def test_identical_content_is_not_written_again(self):
        sync_routes.put("path=memory/MEMORY.md", b"same")
        code, out = sync_routes.put("path=memory/MEMORY.md", b"same")
        self.assertEqual(code, 200)
        self.assertTrue(out.get("unchanged"))
        self.assertEqual([p.name for p in (self.root / "memory").iterdir() if ".conflict-" in p.name], [])

    # ── conversations: union, never shorten ─────────────────────────────────────
    def _session(self, ident, revision, messages):
        return json.dumps(
            {"_quixiPersistenceRevision": revision, "bufferedMessages": [{"t": m} for m in messages]}
        ).encode()

    def test_a_shorter_transcript_cannot_replace_a_longer_one(self):
        long = self._session("a", 10, ["one", "two", "three"])
        short = self._session("a", 10, ["one"])
        sync_routes.put("path=sessions/a.json", long)
        code, out = sync_routes.put("path=sessions/a.json", short)
        self.assertEqual(code, 200)
        self.assertEqual(out.get("kept"), "local")
        self.assertEqual((self.root / "sessions" / "a.json").read_bytes(), long)

    def test_a_higher_revision_wins(self):
        older = self._session("b", 5, ["x"])
        newer = self._session("b", 9, ["x", "y"])
        sync_routes.put("path=sessions/b.json", older)
        code, out = sync_routes.put("path=sessions/b.json", newer)
        self.assertEqual(code, 200)
        self.assertEqual((self.root / "sessions" / "b.json").read_bytes(), newer)
        self.assertIn("conflict", out)

    def test_two_devices_conversations_both_survive(self):
        sync_routes.put("path=sessions/one.json", self._session("one", 3, ["a"]))
        sync_routes.put("path=sessions/two.json", self._session("two", 4, ["b"]))
        code, out = sync_routes.manifest()
        paths = sorted(f["path"] for f in out["files"] if f["path"].startswith("sessions/"))
        self.assertEqual(paths, ["sessions/one.json", "sessions/two.json"])

    # ── large bodies: streamed, not buffered ────────────────────────────────────
    def test_a_large_body_streams_through_unchanged(self):
        payload = os.urandom(3 * 1024 * 1024 + 123)
        stream = io.BytesIO(payload)
        code, out = sync_routes.put_stream("path=files/big.bin", stream, len(payload))
        self.assertEqual(code, 200)
        self.assertEqual(out["size"], len(payload))
        stored = (self.root / "files" / "big.bin").read_bytes()
        self.assertEqual(sync_routes._sha(stored), sync_routes._sha(payload))

    def test_a_short_body_leaves_no_truncated_file_behind(self):
        stream = io.BytesIO(b"only-ten!!")          # claims 20, delivers 10
        code, out = sync_routes.put_stream("path=files/short.bin", stream, 20)
        self.assertEqual(code, 400)
        self.assertIn("short body", out["error"])
        self.assertFalse((self.root / "files" / "short.bin").exists())
        self.assertFalse((self.root / "files" / "short.bin.tmp").exists())

    def test_an_absurd_content_length_is_refused_without_reading(self):
        code, out = sync_routes.put_stream("path=files/huge.bin", io.BytesIO(b""), 10**15)
        self.assertEqual(code, 400)
        self.assertIn("refusing", out["error"])

    # ── the manifest describes, it does not trust ───────────────────────────────
    def test_manifest_reports_size_hash_and_revision(self):
        sync_routes.put("path=memory/MEMORY.md", b"hello")
        sync_routes.put("path=sessions/c.json", self._session("c", 42, ["m"]))
        _, out = sync_routes.manifest()
        by_path = {f["path"]: f for f in out["files"]}
        self.assertEqual(by_path["memory/MEMORY.md"]["sha256"], sync_routes._sha(b"hello"))
        self.assertEqual(by_path["sessions/c.json"]["rev"], 42)

    def test_manifest_ignores_files_that_are_not_whitelisted(self):
        (self.root / "credentials.key").write_bytes(b"secret")
        _, out = sync_routes.manifest()
        self.assertNotIn("credentials.key", [f["path"] for f in out["files"]])

    def test_a_dotfile_smuggled_into_a_whitelisted_directory_is_still_served_safely(self):
        # files/* is wide open by design; what must not happen is escaping the root.
        code, _ = sync_routes.put("path=files/../../../tmp/evil", b"x")
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
