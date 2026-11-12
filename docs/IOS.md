# Doing this on iOS

Nothing here is iOS code. This is what someone would need to know to build one, written by someone who
has just spent the day porting the Android half and would rather you did not repeat the dead ends.

## Start here: the foundation that already exists

The Android half is not a sketch — it is the working reference for every one of these problems, and none
of it is hidden. Read these before writing anything, in this order.

| Read this | Because it answers |
|---|---|
| `app/src-tauri/src/lib.rs` | how the engine is brought up inside a mobile process, how the persona and memory are seeded on first run, how the app talks to the engine over its own IPC |
| `app/src-tauri/src/mail_bridge.rs`, `mail_jobs.rs` | how mail is read by driving the provider's page, when the platform has no IMAP — the same trick works with `WKWebView` |
| `app/src-tauri/src/sync.rs` | the phone side of the sync configuration (the convergence itself lives in the engine's `quixi-mobile` crate) |
| `app/src-tauri/src/capabilities.rs` + the Kotlin `CapabilityPermissions.kt` | how optional permissions are declared but never requested until a person flips a switch — `Contacts`, `Photos`, `CoreLocation` have the same shape |
| `app/ui/` | the entire interface: it is a web view, and this is the JavaScript. WKWebView runs it unchanged |
| `build-apk.sh` | what a full build actually does end to end: persona staged, engine cross-compiled, assets refreshed, signed, scanned |

Then the platform pieces, in the order they will bite you:

1. **The engine.** `cargo build --target aarch64-apple-ios` and `aarch64-apple-ios-sim`, `lipo` them into one
   `.a`, link it into the Xcode target. Same crates, no source changes.
2. **The shell.** Tauri v2 supports iOS with the same configuration file; the Rust side is the same code.
   Where Android has Kotlin, iOS has Swift — and the four pieces are: a `WKWebView` host, `BGTaskScheduler`
   for the hourly sync, `CoreLocation`/`Contacts` for the optional capabilities, and a `URLSession`-based
   bridge for mail instead of the loopback HTTP bridge.
3. **The build.** Xcode will insist on signing, a provisioning profile and a paid account before anything
   runs on a phone. That wall is the reason there is no `.ipa` here, and it is not something a README can
   port around.

**What you will not get from me:** a build, a signing identity, or an App Store submission. What you will get:
every question answered, and the Android side kept clean enough to copy from.

## What carries over for free

The hard part of this app — the engine, the tools, the mail client, the sync protocol — is Rust with a C
ABI. Rust compiles for iOS as well as Android, so a large fraction of the work is a rebuild rather than a
rewrite.

| Piece | Ports as | Notes |
|---|---|---|
| The engine | a `.a` for arm64 + arm64-simulator | `cargo build --target aarch64-apple-ios` and `aarch64-apple-ios-sim`, then `lipo` them together |
| The mail client, the tools | unchanged | same crates |
| The sync client | unchanged | plain TCP + JSON, no platform API in it |
| The persona and memory | unchanged | they are files |
| The UI | a web view | WKWebView instead of Android's WebView; the JavaScript is the same |

## What does not

### 1. Getting it onto a phone

Android lets a person install a file they were given. iOS does not. Your realistic options:

* **App Store / TestFlight** — requires an Apple Developer account (99 USD/year) and review. A review
  will ask about the mail feature (see below).
* **TestFlight** — the same account, up to 10 000 testers, review is lighter but still exists.
* **Side-loading with a free developer certificate** — 7 days before the app stops launching, and
  requires a computer running Xcode at each renewal. Fine for development, not for a person in a kitchen.
* **Enterprise/MDM** — only if you are an organisation.

There is no equivalent of "send them the APK". Plan for that before writing code.

### 2. Background execution

Android's answer was WorkManager with an unmetered constraint. The iOS equivalent is **BGAppRefreshTask**
or **BGProcessingTask**: the system decides when, you get no guarantee of frequency, and it can stop
entirely if the person rarely opens the app. It is not a cron job and it does not run hourly.

The honest design is the same as the Android one anyway: sync on foreground, plus a background task that
uses `NWPathMonitor` to notice "a new network, is the desktop there?" and gives up in seconds if not.

### 3. Driving a web page for mail

**This is the part that will get refused.** On Android the app drives the provider's sign-in page inside
its own web view. On iOS, App Store Review Guideline 4.0 and the associated web-content rules make an app
that automates a third party's site a hard sell — the common reading is that it looks like an unofficial
client of somebody else's service.

If the goal is a working app rather than a store listing, this is a non-issue: you distribute via
TestFlight or side-load and it is nobody else's business. If the goal is the App Store, plan to ship the
IMAP/SMTP path only and let the page-driven route be a build-time option that is off in the review
build.

### 4. Sandboxing

iOS apps are sandboxed more tightly than Android's private storage. The engine expects a writable home
directory it can lay out (`persona.md`, `memory/`, `sessions/`). Point it at the app's Application Support
directory and it works — the mobile layer already takes the state directory as an argument for exactly
this reason.

Where it will bite: a background task may not be able to write where the foreground app did unless the
container is shared correctly. Use one file container for both and do not put anything in Caches that
must survive.

### 5. The rest of the platform

| Android thing | iOS equivalent | Care needed |
|---|---|---|
| Tauri Android shell | Tauri iOS shell (v2 supports it) | new enough that you should expect to fix things |
| `adb` for debugging | Xcode + `devicectl` | no wireless equivalent as simple as `adb pair` |
| Screenshots via `adb exec-out screencap` | `xcrun simctl io … screenshot` on the simulator; Xcode device screenshots on hardware | the guide's capture script would need a second implementation |
| `systemd`-ish daemons on desktop | launchd | the sync daemon is Python either way |

## A port order that will not waste your week

1. **Get the engine building for iOS** and prove it on a simulator with a hard-coded prompt, exactly the
   way the Android port was proved: one turn, real output, no UI. If the engine does not run, nothing
   else matters.
2. **Wrap it in Tauri iOS** and get the existing web UI to render. It will look wrong; it will also prove
   the bridge.
3. **Move the sync client across** and sync against the same desktop daemon. It speaks plain HTTP and
   has no platform dependencies — this should take an afternoon, and it is a good test that the protocol
   really is portable.
4. **Persona and memory** come for free once the state directory is writable.
5. **Mail last, and decide the distribution question before you start it.** Page-driving versus IMAP is a
   distribution decision as much as a technical one.
6. **Then the guide.** The screenshots are device-specific and will need re-taking; the words mostly
   survive.

## What to keep from the Android port

* **One web view.** Do not try to open a second one for mail. Every platform makes this painful.
* **Stream everything.** Bodies to disk in chunks; hashing streamed; no whole-file allocations.
* **The 3-second connect.** A desktop that is off must fail fast, or "is it here?" is unanswerable.
* **Conflict copies instead of merges.** This is platform-independent and it is the single decision that
  stops a sync from being scary.
* **A persona as a build input**, not a hard-coded string.

## If you get it working

Two things would make this repository better rather than fork it:

1. The engine's build recipe for iOS, in the same shape as the Android one, with the versions that
   actually worked.
2. A note on whether the page-driven mail route survived review, and what you told them. That answer is
   worth more than the code.
