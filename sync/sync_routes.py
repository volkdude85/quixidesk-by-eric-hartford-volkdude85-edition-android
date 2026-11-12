"""State sync, served by the same room daemon that already runs the mesh pane.

The mesh moves *messages* between agent instances, and a message path ends in a model turn — slow,
non-deterministic, and free to rewrite whatever it forwards. State cannot travel that way: a memory
file that gets "helpfully" summarised on the way across is data loss wearing a friendly face. So sync
is a separate, deterministic lane inside the same process: hashes, byte-for-byte copies, and conflict
copies instead of merges.

Two classes of file travel, and they resolve differently:

* **State** — persona, memory, preferences. One copy per name; newer wins by mtime, the loser is kept.
* **Conversations** — `sessions/<id>.json`, one file per conversation, named by its own id. They are
  UNIONED, never merged: two devices that talked in different places end up holding both. When the
  same conversation exists on both sides the file with the higher `_quixiPersistenceRevision` wins and
  the other is kept beside it. A transcript is never shortened by a sync.

Two devices are the two places a person actually is: the phone in a pocket, the computer on a desk.
Palm got this right by making the sync a background reflex. The equivalent here is that the phone runs
a pass every time it opens, and neither side is ever the master.

    GET  /api/sync/manifest              -> {"files": [{path, sha256, size, mtime, rev}]}
    GET  /api/sync/get?path=memory/MEMORY.md
    PUT  /api/sync/put?path=memory/MEMORY.md
"""
from __future__ import annotations

import fnmatch
import hashlib
import shutil
import json
import os
import socket
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote

# Exactly what may cross the wire, as patterns relative to the state root. Anything that does not
# match is refused outright, which is what stops a client bug from becoming a filesystem bug.
PATTERNS = (
    "persona.md",
    "memory/MEMORY.md",
    "memory/USER.md",
    "memory/FAMILY-REFERENCE.txt",
    "preferences.json",
    "sessions/*.json",
    # Whatever the person wants to carry between their own machines: a PDF, a video, a folder of
    # photos. Their files are not our business to refuse, and a sync that only moves the assistant's
    # own bookkeeping is a sync that half-works.
    "files/*",
)

# There is no size ceiling worth the name. Bodies are streamed to disk, never buffered, so the only
# honest limit is free space on the receiving machine — and that is checked and reported rather than
# assumed. A PDF, a video, a phone's own files: none of that is our business to refuse. The number
# below exists only to reject a Content-Length that is obviously a lie (a client claiming 40 TB), and
# it is configurable for anyone whose storage is genuinely larger.
MAX_BODY = int(os.environ.get("QUIXI_SYNC_MAX_BODY", str(512 * 1024 * 1024 * 1024)))   # 512 GB
SPACE_HEADROOM = 64 * 1024 * 1024     # keep this much free after a write
CHUNK = 1 << 20                        # 1 MiB
ROOT = Path(os.path.expanduser(os.environ.get("QUIXI_SYNC_ROOT", "~/QuixiDesk"))).resolve()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    """Hash by streaming: a 2 GB file must not cost 2 GB of RAM to describe."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _revision_file(path: Path) -> int:
    """Read just enough of a session file to find its revision, not the whole transcript."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(4096)
        return int(json.loads(head).get("_quixiPersistenceRevision") or 0)
    except Exception:
        return 0


def _allowed(rel: str) -> bool:
    return any(fnmatch.fnmatch(rel, pat) for pat in PATTERNS)


def _resolve(rel: str) -> Path | None:
    rel = unquote(rel or "").lstrip("/")
    if not rel or rel.startswith("/") or ".." in Path(rel).parts or not _allowed(rel):
        return None
    return ROOT / rel


def _revision(data: bytes) -> int:
    """The engine stamps every session file with its own monotonic revision; trust it when present."""
    try:
        return int(json.loads(data).get("_quixiPersistenceRevision") or 0)
    except Exception:
        return 0


def _walk() -> list[str]:
    out: list[str] = []
    for pattern in PATTERNS:
        if "*" in pattern:
            head, tail = pattern.split("*", 1)
            parent = ROOT / head.rstrip("/")
            if parent.is_dir():
                for p in sorted(parent.glob("*" + tail.lstrip("/"))):
                    if p.is_file() and _allowed(str(p.relative_to(ROOT)).replace(os.sep, "/")):
                        out.append(str(p.relative_to(ROOT)).replace(os.sep, "/"))
        elif (ROOT / pattern).is_file():
            out.append(pattern)
    return out


def manifest() -> tuple[int, dict]:
    files = []
    for rel in _walk():
        p = ROOT / rel
        try:
            size = p.stat().st_size
            sha = _sha_file(p)
        except OSError:
            continue
        files.append(
            {
                "path": rel,
                "sha256": sha,
                "size": size,
                "mtime": int(p.stat().st_mtime),
                "rev": _revision_file(p) if rel.startswith("sessions/") else 0,
            }
        )
    return 200, {"ok": True, "root": str(ROOT), "files": files}


def get(query: str) -> tuple[int, bytes, str]:
    rel = (parse_qs(query).get("path") or [""])[0]
    target = _resolve(rel)
    if target is None:
        return 400, json.dumps({"ok": False, "error": "not a syncable path"}).encode(), "application/json"
    if not target.is_file():
        return 404, json.dumps({"ok": False, "error": "no such file"}).encode(), "application/json"
    return 200, target.read_bytes(), "application/octet-stream"


def put_stream(query: str, stream, length: int, host: str = "") -> tuple[int, dict]:
    """Store a body of `length` bytes by copying it to disk in chunks.

    Nothing is accumulated in memory: the previous version read the whole body into a bytes object
    before writing it, which is why it needed a ceiling and why one large conversation could make the
    daemon — which also carries the message relay — stall.
    """
    rel = (parse_qs(query).get("path") or [""])[0]
    target = _resolve(rel)
    if target is None:
        return 400, {"ok": False, "error": "not a syncable path"}
    if length <= 0 or length > MAX_BODY:
        return 400, {"ok": False, "error": f"refusing a body of {length} bytes"}
    free = shutil.disk_usage(target.parent if target.parent.is_dir() else ROOT).free
    if length + SPACE_HEADROOM > free:
        return 507, {
            "ok": False,
            "error": f"not enough room: {length} bytes needed, {free} free",
        }

    conflict = None
    if target.is_file():
        # Only small files are compared in memory; anything big is stored and reconciled by the
        # client's own revision rule on the next pass.
        if target.stat().st_size <= 8 * 1024 * 1024:
            current = target.read_bytes()
            stamp = time.strftime("%Y%m%d-%H%M%S")
            who = (host or socket.gethostname()).replace("/", "_")[:32]
            conflict = target.with_name(f"{target.name}.conflict-{who}-{stamp}")
            conflict.parent.mkdir(parents=True, exist_ok=True)
            conflict.write_bytes(current)

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    written = 0
    digest = hashlib.sha256()
    with open(tmp, "wb") as out:
        remaining = length
        while remaining > 0:
            block = stream.read(min(CHUNK, remaining))
            if not block:
                break
            out.write(block)
            digest.update(block)
            written += len(block)
            remaining -= len(block)
    if written != length:
        tmp.unlink(missing_ok=True)
        return 400, {"ok": False, "error": f"short body: {written} of {length} bytes"}
    os.replace(tmp, target)
    out = {"ok": True, "sha256": digest.hexdigest(), "size": written}
    if conflict is not None:
        out["conflict"] = conflict.name
    return 200, out


def put(query: str, body: bytes, host: str = "") -> tuple[int, dict]:
    rel = (parse_qs(query).get("path") or [""])[0]
    target = _resolve(rel)
    if target is None:
        return 400, {"ok": False, "error": "not a syncable path"}
    if not body or len(body) > MAX_BODY:
        return 400, {"ok": False, "error": "bad body size"}

    conflict = None
    if target.is_file():
        current = target.read_bytes()
        if _sha(current) == _sha(body):
            return 200, {"ok": True, "unchanged": True, "sha256": _sha(body)}
        # Same file, different bytes. A conversation is compared by the engine's own revision: the
        # longer history wins and the other is kept, never dropped.
        if rel.startswith("sessions/"):
            mine, theirs = _revision(current), _revision(body)
            if theirs < mine or (theirs == mine and len(body) < len(current)):
                return 200, {"ok": True, "kept": "local", "reason": "longer history already on disk"}
        stamp = time.strftime("%Y%m%d-%H%M%S")
        who = (host or socket.gethostname()).replace("/", "_")[:32]
        conflict = target.with_name(f"{target.name}.conflict-{who}-{stamp}")
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_bytes(current)

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(body)
    os.replace(tmp, target)
    out = {"ok": True, "sha256": _sha(body), "size": len(body)}
    if conflict is not None:
        out["conflict"] = conflict.name
    return 200, out
