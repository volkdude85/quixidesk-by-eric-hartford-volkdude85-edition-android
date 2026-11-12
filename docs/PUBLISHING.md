# Publishing this

Everything below is what has to be true before the repository goes public, in order. It exists because
"we'll check it before we push" is how a home address ends up in a git history that cannot be rewritten
without breaking its links.

## The name

**Repository:** `quixidesk-android`
**Title line:** QuixiDesk on Android — volkdude85 edition
**Description (the one-liner GitHub shows):**

> Install guide, desktop sync and build notes for running QuixiDesk on an Android phone. Packaging only —
> the application is Eric Hartford's.

**Topics:** `quixidesk` `android` `rust` `tauri` `sync` `documentation` `sideload` `palm-pilot` `self-hosted`

Names considered and rejected: `quixidesk-android-kit` (kit sounds like a box of parts),
`quixidesk-pocket` (implies it is the pocket *edition* of the app rather than the packaging around it),
`quixidesk-sync` (one of the four things in here, and not the biggest).

## Before the first push

Run the gate, then walk the list. Do not skip the ones marked **irreversible**.

- [ ] `./ci/ci.sh` passes locally. **CI has never run in GitHub until the first push** — a green local
      run is the only evidence you have beforehand.
- [ ] `git status` is clean and the commit history contains no secrets. **Irreversible** once pushed:
      a secret in history is a secret in everyone's clone, even if you delete it in the next commit.
      ```bash
      git log -p | grep -InE 'sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|BEGIN [A-Z ]*PRIVATE KEY|password\s*='
      ```
- [ ] The identifier scan is clean over the working tree **and** over the rendered PDF.
- [ ] No file in the tree is one you would not show a stranger: check `git ls-files` line by line.
      This is the step that catches the personal persona, a save file, a screenshot you forgot.
- [ ] `LICENSE` names a holder. "the QuixiDesk Android kit contributors" is fine; "volkdude85" is also
      fine if you intend to be found.
- [ ] The upstream URL in `README.md` and `CREDITS.md` points at the real project, not a placeholder.
- [ ] No binaries: `git ls-files | grep -E '\.(apk|aab|keystore|jks)$'` returns nothing.
- [ ] `sync/sync_routes.py` and `tests/` are present — the protocol's implementation and its tests
      belong together, and shipping one without the other is worse than shipping neither.

## The push itself

```bash
git remote add origin git@github.com:<you>/quixidesk-android.git
git branch -M main
git push -u origin main
```

Then, immediately:

- [ ] Watch the first CI run. It is the first time the workflow has executed on a fresh machine; expect
      one failure from something the local run did not exercise (a missing package, a Chrome path).
- [ ] Check the rendered artifact from that run — the workflow uploads the guide PDF. If it differs from
      the committed one, the local rebuild is not reproducible and that is worth knowing now.
- [ ] Read the repo page as a stranger: does the description say what it is in one line, and does the
      README's first paragraph make clear whose software this is?

## After it is public

- [ ] **Tag a release** (`v0.1.0-alpha`) with the guide PDF attached. Binaries stay out of the
      repository; a release attachment is a different thing and is allowed to be one.
- [ ] **Pin the CI actions by commit SHA.** Tag references (`@v4`) can be moved by their owner; a SHA
      cannot. This is a supply-chain detail that costs ten minutes and is invisible until it matters.
- [ ] **Enable private vulnerability reporting** and put a sentence in `SECURITY.md` saying where to send
      a problem.
- [ ] **Turn on branch protection** for `main`: CI must pass, force-push off. The history is evidence.
- [ ] **Watch the first issue or PR.** Someone will try to build it on a machine you have not tested and
      say "it does not work". The useful reply is which dependency version they had.

## What never goes in

| Thing | Why |
|---|---|
| a real APK | it embeds whichever persona it was built with, and a real one carries a person's memory |
| a personal persona file | same, and worse — it is the whole identity |
| a `sync.json`, a token, a `.keystore` | credentials by any other name |
| a screenshot with a notification, a mail preview or a lock screen | it is somebody's day in a file |
| a home address in a comment, a commit message, or an issue reply | it is permanent |

## If it goes wrong

If a secret or a personal detail lands in a public repository:

1. **Rotate the secret first.** Rewriting history does not un-leak a key that has been cloned.
2. Then decide about history. For a leak that is already public, a normal redaction commit plus a note
   is honest; a force-push rewrite is a bigger decision and it breaks every fork and link.
3. Say what happened, in one line, in the open. The alternative is that someone else finds it later and
   assumes nobody noticed.
