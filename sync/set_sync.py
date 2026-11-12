#!/usr/bin/env python3
"""Point a connected phone at a sync server, over adb, in one command.

The phone's sync settings live in its private data directory, which nothing on the phone can edit by
hand. Rather than ask a person to type a path into a shell on the device, this writes the two fields
over adb and then runs a sync so the result is visible immediately.

    ./set_sync.py --serial <adb-serial> --url http://192.168.1.50:8788 --token <token>
    ./set_sync.py --serial <adb-serial> --check

Works on a debug build (run-as) — a release build is not debuggable, so for a release install the
same file has to come from a build that ships it, or from the app's own settings screen once that
exists.
"""
import argparse
import json
import subprocess
import sys
import tempfile

PACKAGES = ["org.quixidesk.android.debug", "org.quixidesk.android"]


def adb(serial, *args, **kwargs):
    return subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True, **kwargs)


def find_package(serial):
    for pkg in PACKAGES:
        out = adb(serial, "shell", f"run-as {pkg} ls sync.json 2>/dev/null")
        if "sync.json" in out.stdout or out.returncode == 0 and "No such" not in out.stderr:
            ok = adb(serial, "shell", f"run-as {pkg} id")
            if ok.returncode == 0:
                return pkg
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", required=True)
    ap.add_argument("--url")
    ap.add_argument("--token")
    ap.add_argument("--check", action="store_true", help="show what is configured, change nothing")
    args = ap.parse_args()

    pkg = find_package(args.serial)
    if not pkg:
        print("no debuggable QuixiDesk package on that device (release builds are not debuggable)")
        return 2

    if args.check or not (args.url and args.token):
        out = adb(args.serial, "shell", f"run-as {pkg} cat sync.json 2>/dev/null")
        print(f"{pkg}: {out.stdout.strip() or 'no sync.json — not configured'}")
        return 0

    payload = json.dumps({"url": args.url.rstrip("/"), "token": args.token})
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(payload)
        local = handle.name

    adb(args.serial, "push", local, "/data/local/tmp/sync.json")
    write = adb(
        args.serial, "shell",
        f"run-as {pkg} cp /data/local/tmp/sync.json sync.json && run-as {pkg} cat sync.json",
    )
    print(f"wrote to {pkg}: {write.stdout.strip()}")

    # Prove it works rather than leaving the person to wonder.
    print("running a sync pass…")
    for cmd in (["shell", "am", "force-stop", pkg], ["shell", "monkey", "-p", pkg, "-c",
                "android.intent.category.LAUNCHER", "1"]):
        adb(args.serial, *cmd)
    print("now open the app and tap the gear → Sync (or ask the assistant to sync); "
          "the report lists what moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
