#!/usr/bin/env python3
"""Scan a deliverable for anything that should not leave this machine.

Run before anything is uploaded anywhere. It looks for the classes of detail that have bitten us
before: a home path in a build command, an address in a screenshot, a signed-in mailbox in a figure,
a key pasted into an appendix. Exit code is non-zero when anything is found, so it can gate a push.

    /usr/bin/python3 doxcheck.py guide.html QuixiDesk-Android-Guide.pdf
"""
import re
import sys
import zipfile
import subprocess
from pathlib import Path

PATTERNS = [
    ("email address",        r"[\w.+-]+@[\w-]+\.[\w.]{2,}"),
    ("US phone number",      r"\b(?:\+1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b"),
    ("street address",       r"\b\d{2,5}\s+[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Ln|Lane|Dr|Drive|Blvd)\b"),
    ("home directory path",  r"/home/[a-z][a-z0-9_-]+"),
    ("tilde home path",      r"~/\.(?:hermes|ssh|config|mempalace|android-keys)"),
    ("LAN address",          r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
    ("tailscale address",    r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"),
    ("IMEI-shaped number",   r"\b86\d{13}\b"),
    ("api key / token",      r"\b(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,})\b"),
    ("password literal",     r"(?i)\bpassword\s*[:=]\s*\S{6,}"),
    ("mac address",          r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b"),
]

# Personal names are deliberately NOT hard-coded here: a public scanner that lists the name it is
# hiding is itself the leak. Put them in doxdeny.txt, one per line, and keep that file out of git.
DENY_FILE = Path(__file__).with_name("doxdeny.txt")

ALLOW = [
    # Things that look like a finding but are part of the instructions themselves.
    r"192\.168\.0\.20:8099",     # the example engine address in the text
    r"192\.168\.1\.50",          # the example engine / pairing address in the text
]


def text_of(path):
    p = Path(path)
    if p.suffix == ".pdf":
        return subprocess.run(["pdftotext", "-layout", str(p), "-"],
                              capture_output=True, text=True).stdout
    return p.read_text(errors="replace")


def deny_list():
    if not DENY_FILE.is_file():
        return []
    return [line.strip() for line in DENY_FILE.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def walk(paths):
    """Expand directories so a whole package can be checked with one command."""
    for path in paths:
        p = Path(path)
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file() and child.name != "doxdeny.txt" and child.suffix in {".md", ".txt", ".py", ".sh", ".html", ".cmd", ".pdf"}:
                    yield str(child)
        elif p.is_file():
            yield str(p)


def main(paths):
    findings = []
    paths = list(walk(paths))
    for path in paths:
        body = text_of(path)
        for literal in deny_list():
            for m in re.finditer(re.escape(literal), body, re.IGNORECASE):
                line = body[:m.start()].count("\n") + 1
                findings.append((path, f"denied literal", literal, line))

        for label, pattern in PATTERNS:
            for m in re.finditer(pattern, body):
                hit = m.group(0)
                if any(re.search(allow, hit) for allow in ALLOW):
                    continue
                line = body[:m.start()].count("\n") + 1
                findings.append((path, label, hit, line))

    seen = set()
    unique = []
    for f in findings:
        key = (f[0], f[1], f[2])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)

    if not unique:
        print("CLEAN — nothing in the identifier classes was found")
        return 0

    for path, label, hit, line in unique:
        print(f"{path}:{line}  {label:<20} {hit[:80]}")
    print(f"\n{len(unique)} finding(s) across {len(paths)} file(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
