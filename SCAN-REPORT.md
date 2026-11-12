# Scan report

Run before this package was assembled, and re-run after every change. The scanner is
`tools/doxcheck.py`; it exits non-zero on any hit, so it can gate a push.

## What it looks for

| Class | Why it matters |
|---|---|
| e-mail addresses | one real address in a public repo is a permanent spam target |
| US phone numbers | same |
| street addresses | a home address in a document about a phone is the worst case here |
| home directory paths (`/home/<user>` and dotfile config paths) | leaks a username and, with it, a machine layout |
| LAN addresses (`192.168.x.x`) | identifies a network and, in a screenshot, sometimes a router |
| Tailscale addresses (`100.64–127.x.x`) | a routable private address, worse than a LAN one |
| device serials, IMEI-shaped numbers | identifies one physical phone |
| API keys and password literals (`sk-…`, `ghp_…`, `hf_…`, `password: …`) | grants access |
| MAC addresses | identifies hardware |
| personal names and handles | via `tools/doxdeny.txt`, which is **not** committed |

Personal names are kept out of the scanner's own source on purpose: a public scanner that hard-codes
the name it is protecting is the leak. The deny list lives beside it, gitignored, and is loaded at run
time.

## Result at packaging time

```
$ /usr/bin/python3 tools/doxcheck.py .
CLEAN — nothing in the identifier classes was found
```

## Things that were found and fixed while assembling

| Where | What | Fix |
|---|---|---|
| guide, Part 8 | the example pairing address was a real LAN address | replaced with a documentation address (`192.168.1.50`) |
| guide, Appendix A | build commands used the author's home directory | replaced with `$HOME` / `<repo>` |
| guide, figure 1 | the About screen showed an IMEI | band blurred before the figure was drawn |
| `sync/set_sync.py` | docstring example carried a real device serial | replaced with `<adb-serial>` |
| `tools/capture.sh` | screenshot output path hard-coded to one machine | derived from the script's own location |

## What this scanner cannot see

Pixels. A screenshot can carry an address, a name in a status bar or a signed-in mailbox, and no text
scan will find it. Every figure in this package was therefore inspected by eye before it was kept, and
the raw captures (which do contain a whole screen) are not included here — only the six cropped,
annotated figures are.

## What is deliberately absent

No application binary. A build embeds whichever persona it was compiled with, and a real one carries a
person's memory. Shipping an APK here would either leak that or force a rebuild on every persona
change.
