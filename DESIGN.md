# What was built, and why

Every decision below came from a constraint that showed up in testing, not from a preference. Where a
number is quoted, it was measured on a real device. Where something is unfinished, it says so.

---

## 1. The engine runs inside the APK

**Decision.** The Rust engine is compiled into the application as a static library and called through a
thin C ABI. A turn never opens a socket to another machine.

**Why.** The alternative — a thin client talking to a desktop engine — makes the phone a remote control
for a computer that has to be awake. That fails in exactly the places a pocket assistant is useful:
a car, a waiting room, a house where the desktop is off. It also means the assistant stops working the
moment the person walks out of the door, which is a strange property for something called a companion.

**What it cost.** The APK carries the engine and every tool: 18 MB for the arm64 release. Cold start
measured at 467 ms on the reference phone. Every dependency has to cross-compile for Android, and
anything that reaches for a platform library the NDK does not ship has to be compiled out rather than
hoped for — one full-text index now has a `#[cfg]` and a substratch fallback for precisely this reason.

---

## 2. One web view, and the mail page is driven inside it

**Decision.** The app has a single web view. Reading mail means navigating that view to the provider's
own web page and operating it with synthetic pointer and touch events.

**Why.** Free Proton accounts have no IMAP and no SMTP. The alternatives were: a paid bridge, a private
API that the provider changes without notice (and which broke twice during this work), or driving the
page the way a person does. Only the third works for a normal account, and only the third survives the
provider shipping a new front end.

**What it cost, and what it taught.** A second web view is not available on this platform, so the mail
page and the chat share one view; a job therefore has to remember where the user was standing and put
them back afterwards, which the bridge now does. Returning a result from a remote origin is blocked in
both directions (no app commands from that origin, and mixed-content fetches refused), so results come
back through a URL fragment relay. And the provider only fires Send on trusted input, which is why the
compose path fills every field correctly and still stops one tap short of sending.

**The honest limit:** `mail_send` fills the message; the last tap is the user's. That is the correct
place for the boundary, not a bug to route around.

---

## 3. Tools are declared to the engine, driven by the app

**Decision.** The mail tools live in the engine (`mail_inbox`, `mail_open`, `mail_send`) with a typed
`Job` enum and real JSON schemas. Execution is delegated to a `MailDriver` trait that only the app can
install, because only the app owns a web view.

**Why.** Two things fail otherwise. Tools called directly against a provider API cannot use a
page-driven session; and tools that know how to reach into a web view belong to the process that has
one. The trait keeps the engine testable — the tests install a fake driver and assert the schemas, the
required fields and the refusals.

**What it caught.** The first wiring shipped the tool group disabled by default, so the agent could not
see `mail_inbox` at all and silently reached for the IMAP tool instead, which answers "no mail account
is set up" on a phone with no app password. A tool that exists but is not enabled reads as a broken
feature.

---

## 4. Sync converges; it never overwrites

**Decision.** Phone and desktop exchange a manifest of file hashes. Differing files: the newer copy
wins, and the loser is preserved as `<file>.conflict-<machine>-<timestamp>`. Five paths travel — memory,
persona, preferences. Nothing else does.

**Why.** Two machines that both get used apart will both be edited. Last-writer-wins without a copy is
data loss that the person cannot see happening; asking a person to resolve a merge is worse. Keeping
both is the only option that is safe by default, and it means a sync can never be the reason someone
loses their assistant's memory.

**Measured:** `pushed 3 · pulled 1 · errors 0`, then `pushed 0 · pulled 0` on the next pass. A file
edited on the desktop was pulled on the following pass; the replaced copy stayed on disk.

**What it deliberately does not do:** it is not live. Android will not let an app watch the network
without a permanent notification, so the app syncs when it opens. A nag icon on someone's phone to gain
a few seconds of freshness is a bad trade.

---

## 5. The persona is a build parameter, not a code path

**Decision.** `PERSONA_SRC=… ./build-apk.sh arm64 release` decides which persona is compiled in. The
persona, the bundled skills and the memory files are seeded into the engine's data directory on first
run and never overwritten afterwards.

**Why.** The same application is a different assistant depending on the person it is for. Making that a
build input means one codebase, no forks, no "her version" drifting from "his version". Seeding only
when absent means an update never erases what the person's assistant has learned.

**What it caught.** The memory files were first written to `state/memory`, while the engine reads
`$HOME/.quixi/memory`. The seeding logged success and the assistant knew nothing — the worst kind of
bug, because every indicator said it had worked. It is now written where the engine looks, and verified
by reading it back off the device.

---

## 6. The interface is JavaScript on purpose

**Decision.** The UI stays in the web layer. The Rust side is the engine, the tools, the bridge and the
shell.

**Why.** The boundary is not where the time goes. The RPCs are in-process calls measured in
microseconds; a turn is dominated by prompt tokens sent to a model and by the model's own latency.
Rewriting the interface in Rust would be a large change with no measurable effect on how fast a reply
arrives, and it would throw away the iteration speed that made the mobile layout work at all.

**Where the real performance levers are, in order:** prompt size and prefix stability (persona plus
enabled skills plus history go out every turn, and a provider that caches prefixes rewards a byte-stable
ordering), choice of model service, and only then anything on the device.

---

## 7. The guide is generated, and its claims are checked

**Decision.** Every screenshot is taken from a real device by a script, the callouts are drawn by a
script, and the contents page numbers are measured from the rendered PDF and re-verified for drift.

**Why.** Documentation rots the moment it is hand-made. Two commands regenerate the whole document
after a UI change: `tools/capture.sh` and `tools/build_guide.py`. That is the difference between
documentation that stays true and documentation that is true once.

**And a scanner.** `tools/doxcheck.py` fails on e-mail addresses, phone numbers, street addresses, home
paths, LAN and Tailscale addresses, IMEI-shaped numbers, keys and password literals. It runs over the
whole package and exits non-zero, so it can gate a push. A public artefact is not allowed to carry
somebody's address because nobody looked.

---

## What is genuinely unfinished

| Gap | Why it matters | Where it would go |
|---|---|---|
| Conversation history import | memory file yes, past transcripts no — her assistant starts with its knowledge but not its conversations | a one-time importer, phone or desktop side |
| Sync configuration without a shell | release builds are not debuggable, so the two fields need a UI | Settings → Sync |
| Android Auto | the menu path is documented from the app's own structure, not photographed on a device that has it | a device with Android Auto installed |
| In-app mail send | one tap from done; blocked by trusted-input requirements | the user's own tap, or an accessibility service, which is a bigger decision |
| iOS | nothing exists | someone's move |
