# Developer's notes

The short version, in the words of the person who did the assembly:

> **QuixiDesk by Eric Hartford, volkdude85 edition, Android.** Eric Hartford wrote the software ([QuixiAI/QuixiDesk](https://github.com/QuixiAI/QuixiDesk)). I am the
> smart arse who threw it together in a specific order.

That sentence is the whole attribution policy. It appears in the app's sidebar, on its About panel, in
the README, and here. It is not modesty and it is not a disclaimer — it is the accurate description of
what this is.

## What "threw it together in a specific order" actually meant

Because it is not nothing, and it is not a rewrite either:

* **Compiled the engine for another architecture.** The application assumes a desktop. Android is not
  one: no `$HOME`, no write access outside the app's sandbox, a web view instead of a browser, and a
  process the OS will kill without asking. Getting the same engine to run there is a build problem with
  a dozen sharp edges, and every one of them produced a real failure before it produced a fix.
* **A mobile front end over the same shell.** The interface was designed for a 1100 px desktop window.
  At 412 px it needed its own rules, and at 804×360 (a phone on its side) it needed different ones
  again. None of that is upstream's design.
* **Mail that works without IMAP.** Free Proton has no IMAP and no SMTP. The answer was to drive the
  provider's own page inside the app, which meant solving result-return across origins, one web view
  shared with the chat, and a provider that only fires "send" on trusted input.
* **A sync protocol that converges instead of overwriting.** State resolves by recency with the loser
  kept; conversations are unioned by id and never shortened; the phone asks each known computer in turn
  with a three-second timeout so a machine that is off costs seconds, not a hang.
* **Documentation that regenerates itself**, because hand-made documentation is true exactly once.

## Where to look

| If you want | Read |
|---|---|
| the decisions and what they cost | [`DESIGN.md`](../DESIGN.md) |
| the sync protocol and its guarantees | [`SYNC.md`](SYNC.md) |
| what has actually been checked, and what has not | [`TESTING.md`](TESTING.md) |
| what an iOS port would take | [`IOS.md`](IOS.md) |
| dependencies, required and recommended | [`DEPENDENCIES.md`](DEPENDENCIES.md) |
| the security posture, short enough to read | [`SECURITY-POSTURE.md`](SECURITY-POSTURE.md) |
| browser setup, for a person and for an AI | [`BROWSERS.md`](BROWSERS.md) |
| picking this up cold | [`AI-HANDOFF.md`](AI-HANDOFF.md) |

## Conventions in the tree

* **The persona is a build input.** `PERSONA_SRC=… ./build-apk.sh arm64 release`. One codebase, as many
  assistants as there are people who want one. The default is the personal build; the public edition is
  an explicit choice.
* **State is files.** No database. A sync can compare, copy and keep conflicts precisely because
  everything that matters is a file with a name.
* **Nothing is deleted by a sync.** There is no delete verb. If one is ever added, tombstones go in the
  same commit or somebody will lose their history.
* **Comments explain why, or they are not written.** The code is readable; the reasons are not obvious,
  and they are the part that saves the next person a day.
* **Claim nothing that has not been measured.** Every number in these documents came out of a run, and
  the run is described next to it.

## What is deliberately missing

* No CI badge for the app itself — that repository is separate and not published here.
* No binaries in this repository. A build embeds whichever persona it was compiled with, and a real one
  carries a person's memory.
* No roadmap promises. `docs/BACKGROUND-SYNC.md` and `docs/IOS.md` describe work that has not been done,
  in the language of work that has not been done.
