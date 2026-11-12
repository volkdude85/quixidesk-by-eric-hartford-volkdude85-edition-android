# The background trigger

Today the phone syncs when the app is opened, and when asked. It does not sync while it sits in a
pocket. This is the design for closing that gap, and the honest list of what Android allows.

## What the platform permits

| Approach | Cost | Verdict |
|---|---|---|
| Static broadcast receiver on `CONNECTIVITY_ACTION` | none | **Impossible since Android 8.** Implicit broadcasts are no longer delivered to manifest receivers, so there is no "the network changed" wake-up to hang a sync on. |
| Reading the Wi-Fi name to decide "am I home?" | a location permission prompt for a feature that has nothing to do with location | **Rejected.** It is also the wrong question — see below. |
| Foreground service with a permanent notification | a persistent icon in the status bar, forever | Rejected for a companion app: it is a nag that never goes away, and users learn to swipe them off. |
| **WorkManager, periodic, `UNMETERED` network constraint** | system-scheduled, coalesced, no notification | **Chosen.** The OS batches it with everything else waking up on Wi-Fi, so it does not spin the processor. |
| On app open | none | Already implemented, and it covers the common case: the phone is picked up, it catches up. |

## The right question is not "which network"

The phone does not need to know where it is. It needs to know whether the far machine is reachable,
and that question is answered by trying:

```
connect(desk, 3 s)  ->  refused / timed out / nothing       => the computer is not here
                    ->  accepts, manifest arrives           => sync
```

A three-second connect is cheaper than a Wi-Fi scan and needs no permission. It also behaves correctly
on a network nobody anticipated — a friend's house, a hotel, a phone hotspot — which an SSID allow-list
never does.

## The schedule

* **Hourly**, with an `UNMETERED` constraint. Not every fifteen minutes: the difference in freshness is
  imperceptible and the difference in wake-ups is not.
* **Plus** the existing on-open pass, so the usual case is instant.
* **Backoff on failure**: if a pass fails, the next attempt waits longer (1 h → 2 h → 4 h, capped at 8 h)
  and resets on the first success. A phone that spends a week somewhere else should not spend that week
  attempting hourly.

## What has to change in the code

The blocker is structural, not scheduling: **the sync client currently lives in the app crate, and a
background worker has no app crate to call.** Three steps, in order:

1. **Move `sync.rs` into the shared native library** (the static lib the app links), leaving the Tauri
   command in the app as a thin wrapper. No behaviour changes; this is a move.
2. **Export one C entry point** from that library:
   ```c
   char *quixi_sync_once(const char *state_dir, const char *config_json);   // returns a JSON report
   ```
   The worker hands it the paths and gets back the same report the UI sees.
3. **A `Worker` in the Android host** with the constraint and the periodic request, calling that
   symbol through JNI, writing `sync-status.json` so the app can show what happened while it was shut.

Nothing above requires a new permission, a notification, or a change to the protocol.

## What the person experiences

* Walks into a house where the computer is on: it catches up within the hour, usually on the next pass.
* Walks into a house where it is off: nothing happens, and nothing is said.
* Somewhere else entirely for a week: nothing happens. When they next open the app — or ask why things
  are different on the two machines — the status file gives a true answer rather than a shrug:

  > "We're out of sync. Turn on your computer on the same Wi-Fi and tell me, and I'll catch up."

## What this design refuses to do

* No permanent notification.
* No location permission.
* No wake lock.
* No polling while the phone is in a pocket beyond the hourly job the OS already batches.
