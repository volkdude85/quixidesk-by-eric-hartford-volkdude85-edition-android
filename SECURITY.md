# Security

## What leaves the phone

Only two things ever cross the network, and both are chosen by whoever set the phone up:

1. **Conversation turns** to whichever model service is configured — the persona, the enabled skills
   and the conversation so far, as prompt text.
2. **Mail**, read by driving the provider's own page inside the app. The session cookie stays in the
   app's own web view, the same way it would stay in a browser.

Nothing else is transmitted. There is no telemetry and no update check.

## Credentials

Provider API keys live in the app's private storage on the phone. They are never written to logs, never
included in a sync, and the sync server refuses everything outside a fixed file list.

If you find a key committed anywhere in this repository, treat it as compromised: revoke it first, then
open an issue.

## The sync service

* Binds to the LAN, not the internet. Do not port-forward it.
* Requires `Authorization: Bearer <token>` for every request, including `/health`.
* Serves exactly five paths. Anything else — including `../` traversal — is rejected before it touches
  the filesystem.
* It has no delete operation. A sync can create and replace files; it cannot remove them.

Run it on a trusted network with a long random token. It is a small tool for one household, not a
multi-user service, and it is not hardened as one.

## Reporting

Open an issue describing the problem and, if it is sensitive, ask for a private channel rather than
posting details.
