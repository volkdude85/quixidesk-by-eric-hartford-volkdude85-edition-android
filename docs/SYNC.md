# How the sync works

A phone and a computer hold the same assistant. This is the protocol that keeps them in agreement,
written so that anyone — including a model picking this up cold — can see what it guarantees and why.

## The shape of the problem

Two devices, one person. Both are used, sometimes in different places, sometimes both offline. The
things that must agree:

* **State** — persona, memory, preferences. One copy of each, by name.
* **Conversations** — one file per chat, and there will be many, growing, on both sides.

What must never happen: a sync that loses a conversation, shortens a transcript, or ships a credential.

## Why it is not a chat-channel sync

The same house runs a message relay between agent instances. It is tempting to reuse it — two machines
that already talk, why not let them move files?

Because a message path ends in a model turn. The bytes come back summarised, reordered, or helpfully
rewritten. A memory file that gets condensed in transit is data loss wearing a friendly face, and it
fails silently. Sync is therefore a separate lane in the same daemon: deterministic, hashed, no model
anywhere in the path.

## Discovery: ask the house, don't sniff the network

The phone does not read the Wi-Fi name. It could — with location permission — and it would be wrong
anyway: the question a person actually asks is *is that computer on?*

So a sync pass opens a TCP connection to each configured computer with a **3-second** timeout. Off,
asleep, or simply not on this network all fail the same way and in the same time, with a sentence
instead of a hang:

```
the computer is not answering at 192.168.1.50:8790
```

A person may have more than one computer. `sync.json` holds a list, each with its own token, and the
first one that answers gets the pass:

```json
{"homes": [
  {"name": "study", "url": "http://192.168.1.50:8790/api/sync", "token": "…"},
  {"name": "cabin", "url": "http://10.0.0.20:8790/api/sync",  "token": "…"}
]}
```

A bare `{"url": …, "token": …}` still loads and is treated as one computer, so an older config keeps
working. Measured failover with a dead entry first: **4.7 s for the whole pass**, dead one included.

## The protocol

Three routes on the desktop daemon, all requiring `Authorization: Bearer <token>`:

```
GET  /api/sync/manifest                     -> {"ok":true,"files":[{path,sha256,size,mtime,rev}]}
GET  /api/sync/file?path=memory/MEMORY.md   -> raw bytes
PUT  /api/sync/file?path=memory/MEMORY.md   -> {"ok":true,"sha256":…}
```

`/get` and `/put` are accepted as aliases of `/file`. One pass is: fetch the manifest, walk the union
of both sides' paths, and decide per file.

### What may cross

A whitelist of patterns, matched against the state root — never a path built from anything a client
sends without checking:

```
persona.md
memory/MEMORY.md
memory/USER.md
memory/FAMILY-REFERENCE.txt
preferences.json
sessions/*.json
```

Absolute paths, `..`, and anything not on the list are refused before they touch the filesystem.
**Credentials never sync** — `credentials.key`, `providers.json` and anything under profiles are
deliberately outside the list, because a sync that copies secrets turns one compromised machine into
two.

### How each class resolves

| Class | Rule | Failure mode it prevents |
|---|---|---|
| State | newer `mtime` wins; the losing copy is kept as `<name>.conflict-<machine>-<stamp>` | one device silently erasing what the other learned |
| Conversations | **union** — one file per chat, named by its own id | two devices that talked in different places losing each other's history |
| Same conversation, both changed | higher `_quixiPersistenceRevision` wins; on a tie, the longer file wins; the loser is kept | a transcript being shortened by a device that merely opened the app |

There is no delete operation. A sync can create and replace files; it cannot remove them. Anything
that lost a conflict stays on disk until a person deletes it.

### Sizes

Bodies up to **64 MB**. This is not theoretical: a long conversation with tool output in it reached
22 MB, and an 8 MB ceiling rejected it as a malformed request while the file itself was perfectly
fine.

## When it runs

* **On every app open**, a few seconds after launch — the common case, the phone is picked up.
* **On demand**, through the app's own sync entry point.
* **Hourly in the background** is the intended third trigger and is **not built yet**: it needs the
  client to live in the shared native library so a scheduled worker can call it without the UI. Until
  then, a phone that is never opened does not sync.

## What the phone reports

Every pass writes its outcome to `sync-status.json` beside the app's data: when it ran, which computer
answered, what moved, and if nothing answered, what was tried. Failures stay quiet — the app does not
interrupt — but the state is there so it can be said once, later, in words:

> "We're out of sync. Turn on your computer on the same Wi-Fi and tell me, and I'll catch up."

## Verifying it

Against a live pair, in both directions:

```
pass 1   home:"study"  pushed 3  pulled 1  errors 0
pass 2   pushed 0  pulled 0                       ← converged

desktop: 50 conversations   phone: 50   differing: 0
```

And the failover path, with an unreachable computer listed first:

```
study(off) → ok:false, 3 s timeout
cabin      → ok:true
whole pass: 4,691 ms
```
