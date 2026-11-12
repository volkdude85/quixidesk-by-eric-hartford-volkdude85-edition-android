#!/usr/bin/env python3
"""Render the guide and make its contents page tell the truth.

The numbers in the contents table are measured, not typed: render once, read where each section
actually starts, write those numbers in, render again, and assert nothing moved. A hand-written
contents page is wrong the moment a figure grows.

    /usr/bin/python3 build_guide.py
"""
import re
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # the repository root
GUIDE = ROOT / "docs/guide"
HTML = GUIDE / "guide.html"
PDF = GUIDE / "QuixiDesk-Android-Guide.pdf"

SECTIONS = [
    "What you are installing",
    "Before you start",
    "Getting the app file onto the phone",
    "Allowing the install",
    "Installing and opening it",
    "Turning on Developer options",
    "USB debugging",
    "Wireless debugging",
    "Stop Android from closing it",
    "Give it a brain",
    "Signing in to mail, once",
    "Android Auto",
    "When something goes wrong",
    "Appendix for the assistant",
    "The Windows side",
    "Undoing all of it",
]


def render():
    # Chrome needs different flags when it has no user namespace (a container without privileged
    # namespaces), and the flags come from the environment so the workflow itself stays unchanged:
    # a runner has namespaces, so it passes nothing here.
    extra = os.environ.get("CHROME_FLAGS", "").split()
    subprocess.run(
        [
            "google-chrome-stable", "--headless", "--disable-gpu", "--no-pdf-header-footer",
            *extra,
            f"--print-to-pdf={PDF}", "--virtual-time-budget=8000", f"file://{HTML}",
        ],
        check=True, capture_output=True,
    )


def page_text(n):
    out = subprocess.run(
        ["pdftotext", "-f", str(n), "-l", str(n), str(PDF), "-"],
        check=True, capture_output=True, text=True,
    ).stdout
    return re.sub(r"\s+", " ", out).strip().lower()


def find_pages():
    count = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(PDF)], check=True, capture_output=True, text=True).stdout).group(1))
    pages = {n: page_text(n) for n in range(1, count + 1)}
    # Skip the cover and the contents page itself: the contents page contains every title, so a
    # naive search reports every section starting on page 2.
    body = {n: t for n, t in pages.items() if n > 2}
    found = {}
    for title in SECTIONS:
        needle = re.sub(r"\s+", " ", title).strip().lower()
        for n, text in body.items():
            if needle in text:
                found[title] = n
                break
    return count, found


def stamp(found):
    html = HTML.read_text()
    changed = 0
    for title, page in found.items():
        # The contents rows carry data-sec, so the number is written by position rather than by
        # matching the title inside markup — a link wrapper around the title cannot break it.
        index = SECTIONS.index(title) + 1
        pattern = re.compile(r'(<td class="pg" data-sec="' + str(index) + r'">)[^<]*(</td>)')
        html, n = pattern.subn(lambda m: f"{m.group(1)}{page}{m.group(2)}", html)
        changed += n
    HTML.write_text(html)
    return changed


def main():
    render()
    count, found = find_pages()
    missing = [t for t in SECTIONS if t not in found]
    if missing:
        print("MISSING SECTIONS:", missing)
        return 1
    changed = stamp(found)
    render()
    count2, found2 = find_pages()
    drift = {t: (found[t], found2[t]) for t in found if found[t] != found2[t]}
    print(f"pages: {count} -> {count2}")
    print(f"contents rows updated: {changed}")
    print(f"drift after stamping: {'none' if not drift else drift}")
    for title in SECTIONS:
        print(f"  p{found2[title]:>2}  {title}")
    return 0 if not drift else 1


if __name__ == "__main__":
    sys.exit(main())
