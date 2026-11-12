# Recommended computer setup

What to have on the machine that sits next to the phone. None of it is required to run the app; all of
it is what makes the difference between "it works" and "I can figure out why it doesn't".

Each entry says **why**, **where to get it**, and **what to skip**. Nothing here costs money.

---

## The browser you actually use

**Brave** — [brave.com/download](https://brave.com/download/) (`brave-browser` on Arch, `sudo apt install brave-browser` after adding their repo on Debian/Ubuntu, `brew install --cask brave-browser` on macOS).

Blocks trackers by default, ships a Chromium debugging build worth using, and does not require an
account. Turn off its ad programme in settings if you want the privacy without the crypto.

**Firefox** — [mozilla.org/firefox](https://www.mozilla.org/firefox/) (`firefox`, `brew install --cask firefox`).

The alternative, not the lesser one: real privacy defaults, `about:config`, containers, and the only
mainstream browser whose phone debugging can inspect add-ons.

**Skip**: Chrome and Edge if a person lives in them; a stock Chromium for automation. Setup for both
recommended browsers, including the debugging half: [`BROWSERS.md`](BROWSERS.md).

---

## Talking to the phone

**Android platform tools** (`adb`) — [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools).

One zip, unzip it anywhere, put the folder on your `PATH`. This is how you install a build, read a log,
take a screenshot, or push a file without touching the phone.

```bash
adb devices                    # is it there
adb install -r app.apk         # update in place
adb logcat -d | tail -50       # what just happened
adb exec-out screencap -p > shot.png
```

**Skip** the full Android Studio if all you want is `adb`; the platform-tools zip is 10 MB against
several gigabytes.

---

## A desktop that can hold the other end of the sync

**Python 3** — [python.org/downloads](https://www.python.org/downloads/) (Linux and macOS usually have
it; on Windows, tick **Add python.exe to PATH** during install or nothing will find it).

The sync service is one file and the standard library. No `pip install`, no virtualenv, no service to
register.

```bash
python sync/sync_server.py --root ~/QuixiDesk --token <long random string>
```

---

## Working on the documents

**Headless Chrome** (comes with Brave or Chrome) and **poppler-utils** — `sudo apt install poppler-utils`,
`brew install poppler`, `sudo pacman -S poppler`.

The guide is rendered by a browser and verified by poppler (`pdftotext`, `pdfinfo`, `pdfimages`). Without
poppler the build still runs but cannot check itself.

---

## Optional but genuinely useful

| Tool | Why | Where |
|---|---|---|
| **scrcpy** | mirrors and controls the phone from the desktop over USB, no root | [github.com/Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) |
| **Termux** (on the phone) | a shell on the phone itself; useful when there is no computer | [f-droid.org/packages/com.termux](https://f-droid.org/packages/com.termux/) — F-Droid build, not the Play one |
| **Syncthing** | if you want to move large folders between machines and the built-in sync is too narrow for it | [syncthing.net](https://syncthing.net/) |
| **KeePassXC** | a password store that is a file, so it cannot phone home | [keepassxc.org](https://keepassxc.org/) |
| **Proton Mail / Tuta** | mail that does not read your mail | [proton.me](https://proton.me/), [tuta.com](https://tuta.com/) |

---

## What not to install for this

* **No Docker.** Nothing here needs a container, and a container is another thing that can be down.
* **No Node on the desktop.** It is needed only to build the app, not to run or sync it.
* **No "AI browser" or "agent browser" bundle.** The debugging port and a second profile are the whole
  capability; a third-party wrapper is another party between you and the thing you are driving.
* **No password manager browser extension**, if you already run the desktop app — the extension is a
  second copy of your vault in a place that can be scripted.

---

## A machine to run it on, in one line each

| Machine | Verdict |
|---|---|
| Any Windows 10/11 laptop | fine for the sync service and the guide; the app is built elsewhere |
| Any Linux desktop | the natural home — everything here was built on one |
| An Apple laptop | works for the sync and the docs; building the Android app on it is possible but off the beaten path |
| A Raspberry Pi 4 or better | a perfectly good always-on sync host, and quieter than a desktop |
| An old phone | can be the sync host in a pinch; see the note about fixed addresses in `DEPENDENCIES.md` |
