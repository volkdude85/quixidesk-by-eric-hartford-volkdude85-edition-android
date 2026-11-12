# Credits

> **QuixiDesk by Eric Hartford, volkdude85 edition, Android.**
> Eric Hartford wrote the software. volkdude85 is the smart arse who threw it together in a specific
> order.


## The application is not ours

**QuixiDesk** — the engine, the tool system, the interface this kit documents — is **Eric Hartford's** project — [QuixiAI/QuixiDesk](https://github.com/QuixiAI/QuixiDesk). Everything here exists because that
work is good enough to put in a pocket, and because he builds it in the open where someone else can
carry it somewhere he has not been yet.

If you found this repository first: go and look at his. That is the thing. This is the packaging around
it.

Two things deserve saying plainly, because they would otherwise be easy to miss:

* **The phone port is not a rewrite and not a fork that competes.** It is his design, compiled for a
  different architecture, with a mobile-shaped front end and a sync protocol beside it.
* **Nothing here is redistributed on his behalf.** This repository carries documentation, tooling and a
  sync service written for it — not his source, not his binaries. See `LICENSE` for what covers what.

Errors in the packaging, the guide, the sync or the tooling are ours, not his. If the documentation
disagrees with his code, his code is right.

## Ours

| Piece | What it is |
|---|---|
| `docs/guide/` | the setup guide, its figures, and the scripts that regenerate both |
| `sync/` | the deterministic file-sync service and its Windows launcher |
| `docs/SYNC.md`, `DESIGN.md`, `TESTING.md`, `IOS.md`, `DEPENDENCIES.md`, `SECURITY-POSTURE.md` | the reasoning behind the above |
| `tools/` | capture, annotate, guide build, identifier scan, link check |
| `ci/ci.sh` | the gate that runs all of it |
| `tests/` | the sync protocol's own tests |

## Standing on

* **Howard Hinnant** — the `civil_from_days` algorithm that turns a Unix timestamp into a calendar date
  without a date library. It is thirty lines, it is exact, and it is why this project has no date
  dependency in the mail client.
* **The Rust and Android projects**, for a cross-compilation story that mostly works.
* **The people who write documentation in public** — the ones whose READMEs made this port possible at
  several points where the error messages did not.

## If you fork this

Add your name here for what you changed, and be specific about which is yours. A credits file that
blames nobody is worthless; one that claims credit for somebody else's work is worse.

The full split, file by file and side by side: [`docs/AUTHORSHIP.md`](docs/AUTHORSHIP.md).
