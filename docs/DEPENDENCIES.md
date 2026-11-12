# Dependencies

Three separate things share the name "this project": **the app**, **the sync**, and **these docs**. They
have different appetites, so they are listed apart. Nothing here is a suggestion to install on a phone —
a phone needs none of it.

Status: **alpha.** Versions below are the ones this was built and tested against, not a promise that
nothing else works. Anything that compiles is probably fine; anything two major versions away is not.

---

## 1. To run the app on a phone

| Needed | Why | Notes |
|---|---|---|
| Android 10 or newer | the app draws itself with the system web view and uses APIs that stabilised in 10 | tested on 14, 16 and 17 |
| 1 GB free storage | the app is ~18 MB installed, the rest is room for its own files | more if it will carry your photos and videos |
| A model service, **or** a model server on your LAN | the app ships the engine, not the model | key for a hosted service, or a URL for your own machine |
| Nothing else | no Termux, no Python, no Node, no developer tools | the engine is compiled into the APK |

**Optional, only if you want the extra features:**

| Optional | Why |
|---|---|
| A mail account | reading mail needs the provider's own web page; free Proton works, anything with IMAP works better |
| A desktop on the same network | enables sync |
| Developer options + USB debugging | only for updating or debugging from a computer; costs nothing to leave off |

---

## 2. To build the Android app from source

This is the heavy half. Exact versions matter more here, because the Android toolchain is unforgiving.

| Dependency | Version used | Why it is needed |
|---|---|---|
| **Rust** | 1.90 minimum (`rust-version` in `Cargo.toml`); built with 1.99.1 | the engine, the tools, the mail client and the app shell are all Rust |
| **Android targets** | `aarch64-linux-android`, `x86_64-linux-android` | `rustup target add aarch64-linux-android` — one per architecture you ship |
| **Android SDK** | any current; platform 36 present here | compiles and packages the APK |
| **Android NDK** | 29.0.14206865 | the engine is a native library; the NDK is its cross-compiler |
| **JDK 21** | 21.0.13 | Gradle 9.6.1 does **not** run on JDK 27; a newer system JDK fails the build with a Gradle error that does not mention Java |
| **Tauri CLI** | v2 | the shell that hosts the web view |
| **Node.js** | only for that CLI | the app's own UI is plain JavaScript, no bundler |

Three environment variables cause almost every failed first build:

```bash
export JAVA_HOME=$HOME/jdk21          # not the newest JDK on the machine
export CARGO_HOME=$HOME/.cargo       # must be the toolchain that holds the Android targets
export NDK_HOME=$ANDROID_HOME/ndk/29.0.14206865
```

Cross-compiling a native library needs the NDK linker named explicitly, or cargo silently uses the
host compiler and the link fails with a wall of undefined symbols:

```bash
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android24-clang
```

Then:

```bash
./build-apk.sh arm64 release      # -> dist/QuixiDesk-arm64-release.apk
./build-apk.sh x86_64 debug       # -> an emulator build you can debug
```

The script rebuilds the engine first, because Tauri will happily package a stale one and report success.

---

## 3. To run the desktop half (sync)

Deliberately dependency-free — that is the point. On a machine you are handing to someone who will never
open a terminal, "install nothing" is the only acceptable install.

| Needed | Why |
|---|---|
| **Python 3.8+** | runs `sync/sync_server.py`. Standard library only. |
| Nothing else | no Node, no packages, no virtualenv, no service manager |

Start it:

```bash
python sync/sync_server.py --root ~/QuixiDesk --token <a long random string>
```

Windows: double-click `sync/windows/start-sync-server.cmd` after putting your token in it.

If you already run the room daemon that holds the mesh pane, the same routes are served from there and
you do not need this file at all — see `docs/SYNC.md`.

---

## 4. To work on this documentation

| Needed | Why | Notes |
|---|---|---|
| **Python 3** | `tools/`, `ci/ci.sh`, `tests/` | standard library only; no `pip install` anywhere |
| **Headless Chrome** | renders the guide PDF | any recent Chromium; the workflow installs `chromium-browser` |
| **poppler-utils** | `pdftotext`, `pdfinfo`, `pdfimages` — how the guide verifies itself | `apt install poppler-utils` |
| **A device or emulator** | re-taking the screenshots | `adb` from the Android platform tools |

Nothing needs a build step or a package manifest, which is deliberate: a documentation pipeline with a
lockfile is a documentation pipeline that rots.

---

## 5. Recommended, not required

Opinions, clearly marked as opinions:

* **A recent Chromium-derived browser** for the live UI preview. The app *is* a web view; the preview is
  the real thing resized.
* **`adb` on the PATH** before you need it. Every "why did my build fail" ends with wanting a log.
* **A second phone** that is not the one you love. Debug builds are called debug for a reason.
* **A desktop on the same Wi-Fi with a fixed LAN address.** DHCP moving the address is the single
  most common cause of "sync stopped working".
* **A long random token**, generated once and written down somewhere that is not the repository:

  ```bash
  head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 28
  ```

---

## 6. What is deliberately not a dependency

* **No cloud service.** No account is required to run the app or to sync.
* **No database.** State is files.
* **No package manager at runtime.** Nothing is fetched and executed on the device.
* **No telemetry, no analytics, no update check.**
* **No LLM bundled.** A model is a choice the person makes, not something shipped inside the app.

---

## 7. Known-bad combinations

Collected so nobody rediscovers them:

| Combination | Symptom | Do this instead |
|---|---|---|
| Gradle 9.6.1 + JDK 27 | build fails with a Gradle message that never says "Java" | `JAVA_HOME` to JDK 21 |
| `CARGO_HOME` pointing at a toolchain without the Android targets | *"can't find crate for `core`"* | point it at the toolchain that was `rustup target add`ed |
| Tauri pointing at a system Python for its own tooling | odd import errors during the build | build inside a clean environment |
| Android's own `libsqlite.so` vendored into the APK | `dlopen failed: library "libandroidicu.so" not found` | do not vendor it; the full-text index is compiled out on Android |
| Screenshots taken from the desktop with a device mirrored | status bar, notifications, and whatever else was on screen | capture on the device, crop to the app surface |
