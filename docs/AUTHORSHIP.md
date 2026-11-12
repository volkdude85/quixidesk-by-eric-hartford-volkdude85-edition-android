# Who wrote what

Two people made this, and it would be wrong to blur them together. The software is Eric Hartford's. The
Android packaging, the sync and the guide are volkdude85's. Nothing below is a guess: the left column is
what the upstream repository contains, and the right column is what was written in this one.

---

## Eric Hartford — QuixiDesk

Everything that makes it an assistant rather than an Android app:

| What | Where it lives upstream |
|---|---|
| The engine: model loading, inference, sampling, streaming | `crates/quixi-engine` |
| The agent loop — turns, tool calls, context assembly | `crates/quixi-ipc`, `crates/quixi-mcp` |
| The tool system: files, shell, search, calendar, mail | `crates/quixi-mcp` |
| Cordis — the workspace/plugin layer and its index | `crates/quixi-cordis` |
| Platform services behind one interface | `crates/quixi-platform` |
| The desktop application and its interface — every screen in this app's UI | `app/ui`, `app/src-tauri` |
| The licence that makes any of this legal to ship | MIT, upstream `LICENSE` |

The interface in the screenshots is his design. The layout, the composer, the sidebar, the settings
panels, the colour system, the copy — that is his work, carried across intact. Where the phone needed
something different, it was changed in place and noted below, not rebuilt.

Upstream: <https://github.com/QuixiAI/QuixiDesk>

---

## volkdude85 — the Android edition

The port, the sync, and the paperwork. Written for this repository:

### Making it run on a phone

- **The Android shell.** A Tauri v2 application wrapping upstream's UI, built for `aarch64` and
  `x86_64` with the NDK, with the engine linked **into the APK** so the phone works with no computer
  present. That was the constraint the whole thing was built around.
- **The engine port.** Upstream's engine crosses to Android in this tree: the `sqlite3` boundary had to
  be gated (the platform's `libsqlite.so` is a private library that drags `libandroidicu.so` in once
  bundled), the Cordis index falls back to substring search on Android, and `api_server` and the CLI
  had to learn upstream's `StreamChunk::ToolCallPrepared` variant.
- **The IPC bridge.** The EIPC channel envelope was one `$_` short, which silently returned `null` for
  every session call — no error, no session, a dead composer.
- **The mobile layout.** Compact rules for narrow and short viewports, a composer that stays above the
  keyboard, the top bar reduced to icons where the width runs out, and a landscape mode that doesn't
  render a desktop layout into 360 px of height.
- **The input layer.** `human.js` — a step library that drives the page the way a person would (real
  pointer, touch and key events with realistic timing), so automation on a phone is input rather than
  injection.
- **Mail on the device.** A driver installed into the engine's tool layer at startup, plus a loopback
  bridge with a bearer token, so the mail tools answer inside the APK.

### Sync — the part that did not exist

- **The protocol.** `GET /manifest`, `GET /get`, `PUT /put` on the existing room daemon, byte-exact,
  token-gated, loopback-only unless a token is set. Conversations are **unioned**; state resolves
  newest-wins with the loser kept beside the winner. Nothing is ever summarised on the way across.
- **The client.** State and session convergence, multi-computer failover in three seconds, streamed
  uploads that never hold a whole file in memory, and offset-based resume so a dropped transfer
  continues instead of restarting.
- **Running without the app.** The sync client lives in the shared native library behind one entry
  point, so a WorkManager job (hourly, unmetered-only, exponential backoff) can converge memory and
  conversations with no window open.
- **Setting it up from the phone.** Three fields and a button in Settings. Tokens are never rendered
  back, so the screen is safe to photograph.

### Shipping it

- **Persona and memory as build inputs.** `PERSONA_SRC=` builds a different assistant from one
  codebase; bundled memory and skills seed once, and never overwrite what the person has since written.
- **The install guide.** A designed PDF with annotated screenshots: developer options, unknown
  sources, battery exceptions — the parts that stop a normal person.
- **The checks.** A dox scanner for the package (emails, phone numbers, addresses, home paths, LAN and
  Tailscale addresses, serials, keys, passwords), a link checker that runs with the network on, and CI
  that runs both plus the packaging checks on every push.
- **The voice.** The rotating title line and the working commentary — the jokes land on the software,
  never on the person using it. Written for shits and grins: if it ever lands badly, the apology is in
  the README and the lines are one array in one file.

---

## What neither of us wrote

The models are other people's work. The provider is your choice at runtime. The phone's operating
system, the browser, the NDK, the Rust toolchain, the crates in `Cargo.lock` — all somebody else's, all
credited by their own licences, none of them redistributed here.

If you find a mistake in the packaging, it is volkdude85's. If the assistant itself behaves badly, that
is a conversation for the upstream project.
