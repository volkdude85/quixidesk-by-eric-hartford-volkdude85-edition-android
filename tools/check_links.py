#!/usr/bin/env python3
"""Every link in the documentation has to point at something.

Internal links are checked against the filesystem; external ones are fetched when --net is given, so
the default run stays offline and deterministic while the scheduled run can catch a dead URL.

    /usr/bin/python3 tools/check_links.py            # offline
    /usr/bin/python3 tools/check_links.py --net      # also HEAD every https:// link
"""
import re
import sys
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP = ("mailto:", "tel:", "#")

def main() -> int:
    net = "--net" in sys.argv
    bad, checked = [], 0
    for doc in sorted(ROOT.rglob("*.md")):
        if ".git/" in str(doc):
            continue
        text = doc.read_text(errors="replace")
        for target in LINK.findall(text):
            target = target.split()[0].strip("<>")
            if target.startswith(SKIP):
                continue
            checked += 1
            if target.startswith(("http://", "https://")):
                if not net:
                    continue
                try:
                    req = urllib.request.Request(target, method="HEAD",
                                                 headers={"User-Agent": "quixidesk-ci"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        if r.status >= 400:
                            bad.append((doc, target, f"HTTP {r.status}"))
                except Exception as error:                       # noqa: BLE001
                    bad.append((doc, target, str(error)[:80]))
                continue
            resolved = (doc.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                bad.append((doc, target, "missing on disk"))
    print(f"checked {checked} link(s) in the documentation")
    for doc, target, why in bad:
        print(f"  BROKEN {doc.relative_to(ROOT)} -> {target}  ({why})")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
