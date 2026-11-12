#!/usr/bin/env python3
"""The desktop half of the phone sync — one small HTTP service, no dependencies.

Design rules, and why each one is there:

* **Neither side is the master.** Both ends run the same rules over a manifest of file hashes: the
  newer copy wins, and the older one is kept beside it instead of being destroyed. Two machines that
  both wrote while apart therefore CONVERGE on the next meeting instead of one silently eating the
  other's work.
* **Only small state files travel.** Memory, persona, preferences. Not the model, not the workspace,
  not the conversation database — those are large, and a half-synced session store is worse than none.
* **A token, always.** It refuses to serve without one, and it only listens on the LAN.
* **No dependencies.** Python 3 on Windows ships with everything this needs, so "install the sync
  server" is "run this file", not "install Node and a build toolchain".

Run it:
    python sync_server.py --root "%USERPROFILE%\QuixiDesk" --token <something-long>

Endpoints (all require Authorization: Bearer <token>):
    GET  /health                     -> {"ok": true, "root": ...}
    GET  /manifest                   -> {"files": [{path, sha256, size, mtime}, ...]}
    GET  /file?path=memory/MEMORY.md -> raw bytes
    PUT  /file?path=memory/MEMORY.md -> stores the body, returns {"sha256": ...}
"""
import argparse
import hashlib
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# The only things that sync. Anything else on either side is left alone.
SYNCABLE = [
    "memory/MEMORY.md",
    "memory/USER.md",
    "memory/FAMILY-REFERENCE.txt",
    "persona.md",
    "preferences.json",
]

MAX_BODY = 4 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Handler(BaseHTTPRequestHandler):
    server_version = "QuixiSync/1"
    root: Path = Path(".")
    token: str = ""

    # ---------- plumbing ----------
    def log_message(self, fmt, *args):
        sys.stderr.write("%s  %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _authorised(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return supplied == f"Bearer {self.token}"

    def _send(self, code: int, body: bytes, ctype: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _target(self, raw: str) -> Path | None:
        """Resolve a request path inside the root, refusing anything that escapes it."""
        rel = unquote(raw).lstrip("/")
        if rel not in SYNCABLE:
            return None
        return self.root / rel

    # ---------- routes ----------
    def do_GET(self):
        if not self._authorised():
            return self._json(401, {"error": "bad or missing token"})
        url = urlparse(self.path)

        if url.path == "/health":
            return self._json(200, {"ok": True, "root": str(self.root), "files": len(SYNCABLE)})

        if url.path == "/manifest":
            files = []
            for rel in SYNCABLE:
                p = self.root / rel
                if not p.is_file():
                    continue
                data = p.read_bytes()
                files.append({
                    "path": rel,
                    "sha256": sha256_bytes(data),
                    "size": len(data),
                    "mtime": int(p.stat().st_mtime),
                })
            return self._json(200, {"files": files})

        if url.path == "/file":
            rel = (parse_qs(url.query).get("path") or [""])[0]
            target = self._target(rel)
            if target is None:
                return self._json(400, {"error": "not a syncable path"})
            if not target.is_file():
                return self._json(404, {"error": "no such file"})
            return self._send(200, target.read_bytes(), "application/octet-stream")

        return self._json(404, {"error": "no such route"})

    def do_PUT(self):
        if not self._authorised():
            return self._json(401, {"error": "bad or missing token"})
        url = urlparse(self.path)
        if url.path != "/file":
            return self._json(404, {"error": "no such route"})
        rel = (parse_qs(url.query).get("path") or [""])[0]
        target = self._target(rel)
        if target is None:
            return self._json(400, {"error": "not a syncable path"})

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._json(400, {"error": "bad body size"})
        body = self.rfile.read(length)

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(body)
        os.replace(tmp, target)
        return self._json(200, {"sha256": sha256_bytes(body), "size": len(body)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="folder that holds memory/ and persona.md")
    ap.add_argument("--token", required=True, help="shared secret; the phone must send the same one")
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8790)
    args = ap.parse_args()

    root = Path(os.path.expandvars(args.root)).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    Handler.root = root
    Handler.token = args.token

    print(f"QuixiDesk sync serving {root}")
    print(f"  on http://{args.bind}:{args.port}   token: {args.token[:6]}… ({len(args.token)} chars)")
    print(f"  files: {', '.join(SYNCABLE)}")
    ThreadingHTTPServer((args.bind, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
