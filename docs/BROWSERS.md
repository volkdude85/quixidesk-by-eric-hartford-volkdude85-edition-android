# Browsers, for people and for the thing driving them

Two jobs are described here and they are not the same:

1. **A browser a person uses** — privacy by default, no telemetry you cannot switch off.
2. **A browser an AI can drive** — a second, isolated instance with a debugging port open, so it can
   look at pages, click things and read what comes back without touching the one you are looking at.

The recommendation is **Brave** for both, and **Firefox** as the alternative, for the same pair of
reasons: they do not sell you by default, and they both ship a debugging package worth using.

Do not use a stock Chromium build for the second job; it works, but its debugging port is a
remote-control socket and its profile carries your logins.

---

## Brave: remote debugging, in order

Brave is Chromium underneath, so the protocol is CDP (the Chrome DevTools Protocol) and every tool that
speaks to Chrome speaks to it.

### 1. A second profile, always

Never turn on remote debugging in the profile you browse with. A debugging port exposes every logged-in
session in that profile to anything that can reach the port.

```bash
mkdir -p ~/.cache/nora-browser
brave-browser --remote-debugging-port=9223 \
              --user-data-dir=$HOME/.cache/nora-browser \
              --no-first-run --no-default-browser-check
```

The `--user-data-dir` is the part that matters. Without it, Brave ignores the flag if an instance is
already running — you get no error and no port, which looks exactly like "the port is blocked".

### 2. Confirm it is listening

```bash
curl -s http://127.0.0.1:9223/json/version | head -5
curl -s http://127.0.0.1:9223/json/list    | python3 -m json.tool | head -20
```

`/json/list` is the list of pages you can attach to. If a page is not there, it is not attachable.

### 3. Attach and drive

Any CDP client works. The smallest useful sequence is: connect to the page's `webSocketDebuggerUrl`,
send `Runtime.evaluate` with `expression: "document.title"`, read the result.

Practical notes learned the hard way:

* **Use a port nobody else has claimed.** 9222 is the default every tutorial uses; if a browser of yours
  is already on it you will attach to *your* tabs and read the wrong screen. Pick something like 9223.
* **A port bound to `127.0.0.1` is not reachable from another machine**, which is usually what you want.
  To drive a phone's web view instead, forward it over `adb`:
  `adb forward tcp:9223 localabstract:webview_devtools_remote_<pid>`.
* **Attaching to a page mid-navigation can kill the socket.** Re-check `/json/list` and reconnect rather
  than assuming the browser died.
* **`--headless=new` is fine for scraping**, but not for anything that has to look like a person.

### 4. The UI, if you want one

`brave://inspect/#devices` lists targets and opens DevTools against them. Good for poking; useless for
automation.

---

## Firefox: remote debugging, in order

Firefox dropped CDP in version 129. Anything that says "connect Selenium/Playwright to Firefox over CDP"
is describing a version of Firefox that no longer exists.

The supported paths are **WebDriver BiDi** (modern, bidirectional) and **Marionette** (legacy, still
present). The practical, well-supported route is geckodriver, which speaks both.

### 1. A second profile

```bash
firefox --new-instance --profile "$(mktemp -d)" about:blank
```

Firefox will not open a second instance against a profile that is in use, so `--new-instance` plus a
throwaway profile is the reliable combination.

### 2. Geckodriver

```bash
geckodriver --port 4444          # ships with most distros; otherwise from mozilla/geckodriver releases
```

Then point any WebDriver client at `http://127.0.0.1:4444`. With Selenium:

```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
opts = Options()
opts.binary_location = "/usr/bin/firefox"
driver = webdriver.Firefox(options=opts)      # geckodriver must be on PATH
driver.get("about:blank")
print(driver.title)
```

### 3. About:debugging, for a human

`about:debugging#/runtime/this-firefox` shows what is inspectable. For a *phone's* Firefox:
`about:debugging#/setup` → enable USB devices → `adb forward tcp:6000 localfilesystem:/data/data/org.mozilla.firefox/firefox-debug` → connect. This is the one place where Firefox's phone debugging is genuinely better
than Chromium's: it can inspect add-ons and service workers that CDP cannot see.

### 4. What Firefox is better at

* Real privacy defaults without a vendor's ad programme attached.
* Add-on inspection and `about:config` — you can turn off the parts you do not want and prove it.
* Container tabs: separate logins in one window, which is a cheap way to keep two identities apart.

### 5. What to avoid

* **Chrome** — the debugging story is excellent and the privacy story is not. If it is only for
  automation, fine; if a person is going to live in it, do not.
* **Edge** — same engine, more telemetry, and it will keep asking.
* **Anything with "AI browser" in the name**, until you have read what it sends where.
* **A browser extension that claims to add "remote control"** — you do not need one; the port is the
  control, and an extension is a second party in the middle.

---

## Recommended setup for an AI that drives a browser

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│ your browser                │        │ the AI's browser             │
│ default profile             │        │ --user-data-dir=<temp>       │
│ your logins                 │        │ --remote-debugging-port=9223 │
│ no debugging port           │        │ no logins, no history        │
└─────────────────────────────┘        └──────────────────────────────┘
```

* **Two instances, two profiles, two purposes.** The isolation is the security model, not a nicety.
* **Keep the automation profile disposable.** Delete it when the job is done; do not let a session
  cookie live in a directory anything can attach to.
* **Bind the port to loopback.** `--remote-debugging-address=127.0.0.1` if your build offers it, and never
  port-forward it.
* **Take the screenshot from the automated browser, not the human one.** Asking a person to screenshot
  their own screen for a document puts their notifications, their mail and their family in the file.

## A note for the phone case

The app here *is* a web view, so debugging it is the same protocol with a different door: enable
developer options, then `adb forward tcp:9223 localabstract:webview_devtools_remote_<pid>` and treat it
as a page. Debug builds expose that socket; release builds do not, which is deliberate.
