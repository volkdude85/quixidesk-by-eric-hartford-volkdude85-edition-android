# Security, in the only amount that helps

A full audit produces a document nobody reads and a list of hypotheticals that stops work. This is the
other thing: the short list of ways this **actually** hurts someone, what the answer is today, and what
is deliberately out of scope. Five items, no more.

If something is added that makes one of these worse, it belongs in a review before it merges.

## 1. The sync daemon is reachable from the network

**What could go wrong:** anyone on the same Wi-Fi reads or writes the assistant's memory and files.

**Answer today:** every sync route requires `Authorization: Bearer <token>`; with no token configured the
daemon answers loopback only, so the default is closed rather than open. Paths are checked against a
whitelist, `..` and absolute paths are refused, and there is no delete verb. Verified: `401` without a
token, `not a syncable path` for `../../etc/passwd`.

**What is not covered:** the token travels in clear text over the LAN. On a home network that is a
deliberate trade — TLS with self-signed certificates for a household is a worse experience than the risk
it removes. On a network you do not control, do not sync.

## 2. A credential ends up somewhere it should not

**What could go wrong:** a key in a synchronised file, a screenshot, a log, a commit.

**Answer today:** credentials are outside the sync whitelist by construction (`credentials.key`,
`providers.json` and the profiles directory are not in it), the identifier scanner runs over the whole
package and fails the build, and the release scanner refuses a shipped secret.

**The failure mode to watch:** adding a path to the whitelist "just to make X work". That one line is the
whole risk in this area.

## 3. The phone's data is readable by another app on the phone

**What could go wrong:** a malicious app reads the assistant's memory or its provider keys.

**Answer today:** application-private storage, which on Android is enforced by the OS and not by this
project. Files the sync writes are created inside it.

**What is not covered:** a rooted or compromised device. Nothing in userspace fixes that, and pretending
otherwise wastes everyone's time.

## 4. Mail reading touches someone's real account

**What could go wrong:** credentials or message contents leaking through logs or a screenshot.

**Answer today:** the mail path drives the provider's own page inside the app's web view and never
handles the password itself — it is typed into the provider's form, and the session stays in the web
view the way it would in a browser. Message contents are not written to disk by the sync.

**The rule that follows:** the app never asks for a mail password on a screen it drew.

## 5. A large or hostile request takes the daemon down

**What could go wrong:** one connection stalls or exhausts memory, and the message relay that shares the
process dies with it.

**Answer today:** bodies are streamed to disk in 1 MiB chunks rather than buffered, uploads have a write
timeout, the disk is checked before a write and the answer is `507` with the numbers if it will not fit,
and a short body leaves a temporary file rather than a truncated real one. Measured: 120 MB in and out
with resident memory flat at ~26 MB.

**What is not covered:** rate limiting and connection caps. The threat model is one household on a
trusted network; a public deployment needs both, and that is a different project.

## What this document deliberately is not

* Not a threat model for a hostile internet.
* Not a promise about third-party dependencies.
* Not a substitute for reading the code before trusting it — the whitelist, the token check and the
  path check are each a few lines, and they are meant to be read.

## The one-line rule

**Nothing that leaves the machine may contain a secret, and nothing that arrives may be written
outside a whitelisted path.** Everything else in this file is a consequence of those two.
