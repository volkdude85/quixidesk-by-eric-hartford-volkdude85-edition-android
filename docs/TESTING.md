# How this is tested

Not a description of a process document. The actual procedures, in the order they are run, with the
reason each one exists and the failure it has caught.

The short version: **a claim needs a number, and the number has to come from the real path.**

## 1. Run the real thing, not a harness

A harness proves the harness works. Every check below ran against the shipped artifact — the APK on a
device, the daemon on its real port, the files in their real directories.

Harnesses are allowed only to isolate a suspected cause *before* the fix, never to declare the fix done.

> Worked example: a sync client was "working" in a browser tab while the shipped APK silently sent
> every request to the wrong path. The harness had no server to be wrong about.

## 2. Believe the suite, then find out which side is wrong

When a test fails, the instinct is to assume the code is broken. Often the *test* is.

> Worked example: `civil_conversion_is_right_for_a_known_day` failed, expecting 2026-11-11 for day
> 20 765 and getting 2026-11-08. The conversion was Howard Hinnant's `civil_from_days`, which is
> correct; 2026-11-11 is day **20 768**. The expected value had been copied from the algorithm's own
> output — a test that proves nothing.
>
> Fixed by taking the constants from a real calendar and adding cases that can actually disagree: the
> epoch, a leap day in a century year (2000-02-29), a leap day in an ordinary leap year (2024-02-29),
> and the day after it. `78 passed; 0 failed` where it had been `77 passed; 1 failed`.

The rule that produced this: **any expected value in a test must come from outside the thing under
test.**

## 3. Run it twice — the second pass is the assertion

For anything that converges (a sync, an index, a cache), the first pass shows work happening. The
second pass is what proves it *finished*.

```
pass 1   home:"study"  pushed 3  pulled 1  errors 0
pass 2   pushed 0  pulled 0                     ← this line is the test
```

A system that moves the same files every pass is not syncing; it is looping. Zero on the second pass
cannot be faked by a system that is confused.

## 4. Break a dependency on purpose

Happy paths pass by accident. Each external dependency gets failed deliberately, and the failure has to
be **fast and legible**:

| Deliberately broken | Required behaviour | Measured |
|---|---|---|
| the far machine is off | fail in seconds, name the address | 3 s timeout, *"the computer is not answering at …"* |
| the first of two machines is off | skip it, use the second | whole pass 4,691 ms, `home:"cabin"` |
| the token is wrong | refuse, say so, change nothing | `401 bad or missing token` |
| the path is `../../etc/passwd` | refuse before touching the filesystem | `not a syncable path` |
| the body is short of its Content-Length | delete the partial, refuse | `short body: N of M bytes` |

## 5. Byte-identical, or it did not happen

Any code that moves bytes is checked with a hash of the bytes at both ends, never by looking at a
success message.

```
120 MB in   → sha256 identical, daemon RSS 26.4 → 26.6 MB   (proves it never buffered)
120 MB out  → byte-identical round trip
 40 MB phone → desktop, sha 249a0517… on both ends
 40 MB desktop → phone, files/clip.mp4 : 41 943 040 bytes in 17.2 s
```

Memory is part of the assertion. A transfer that works by allocating the whole body is a transfer that
will fail on a phone, so the resident size is measured before and after.

## 6. Verify layout by geometry, not by opinion

A vision model will describe a screen it cannot read and call a clipped button "fine". Rectangles are
exact, so layout defects are asserted numerically, in the live page:

```js
// the composer's own button row must be inside the window
tools.bottom <= window.innerHeight       // was 305 vs 285 → half the row was cut off
matchMedia('(max-width: 520px)').matches  // is the compact layout actually in force?
getComputedStyle(el).display              // "none" or the rule lost the cascade
```

Vision is used only for what geometry cannot answer: is this the right screen, is the highlight on the
right row.

## 7. Prove an absence, and prove the prover

A scan that reports "clean" is worthless until it has been shown to fail on something dirty.

> The identifier scan was pointed at the package, found four real hits, and every one was fixed. On a
> previous run of the same idea, an APK deliberately poisoned with a password produced two findings
> and failed the build — which is the only reason to believe the clean result.

## 8. Screenshots are generated, and so is what they claim

Every figure comes from a script: capture, crop, annotate. Nothing is edited by hand, so a UI change is
two commands rather than a morning of image work, and the document cannot drift from the product
without the next build showing it.

Contents-page numbers are measured from the rendered PDF and re-checked for drift; the build fails if a
section cannot be found.

## What is not tested

Stated because a list of successes is not a test report:

* **No CI.** Every run above was done by hand, by a person or an agent, and the evidence is in the
  transcript rather than in a pipeline.
* **No long soak.** Nothing has run for days. Memory growth over a week of syncs is unmeasured.
* **No background-trigger test**, because the background trigger does not exist yet.
* **One device family.** An Android 16 emulator, a Pixel on 17, and a OnePlus on 14 — not a fleet, and
  not a low-RAM phone.
* **No hostile network.** Captive portals, packet loss and a Wi-Fi that dies mid-upload are reasoned
  about, not reproduced. That last one is why resume-by-range is on the list.
* **No security review.** The token gate and the path whitelist have tests; the rest of the attack
  surface has not been examined.

## The one-line version

If a claim cannot be shown with a number produced by the shipped code, it is not a claim yet — it is a
hope with a comment above it.
