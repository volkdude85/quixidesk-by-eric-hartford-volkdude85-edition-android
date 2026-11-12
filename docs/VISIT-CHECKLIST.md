# What to take, and the order to do it in

For handing the app to someone else's phone. Written to be followed once, standing in their kitchen.

## Take

- [ ] Her APK, built with her persona: `QuixiDesk-Scintilla-arm64.apk` (or whichever persona is hers)
- [ ] `QuixiDesk-Android-Guide.pdf` — so she keeps the instructions after you leave
- [ ] This laptop, with `sync/sync_server.py` and a token already chosen
- [ ] Your phone or a USB-C cable, whichever gets the file across
- [ ] A model service key for her, if she does not already have one

## Before you sit down

- [ ] Confirm her phone is **arm64** (every phone since ~2016 is) and Android 10 or newer
- [ ] Decide her persona name and check it is the one compiled into her APK — the app shows it in the
      top bar, so this is visible at a glance
- [ ] Choose the sync token now, not in her kitchen:

      head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 28

## On her phone, in this order

1. **Transfer** the APK: cable → Internal storage → Download, or send it to her by mail.
2. **Install** — tap the file, allow from this source, Install, Open.
3. **Developer options** — Settings → About phone → tap Build number seven times.
4. **Wireless debugging** only if you want to update her remotely later; otherwise skip it and leave
   USB debugging off. This is the one step with a security cost, and it is optional.
5. **Battery** — Settings → Apps → QuixiDesk → Battery → Unrestricted. Do not skip this one; without it
   the app is killed in the background and appears to forget things.
6. **Model service** — gear → pick a service or enter your own engine's address, paste the key, choose
   a model. Send one message and confirm a reply comes back before moving on.
7. **Mail**, if she wants it — ask the assistant to check mail, sign in on the page it opens, clear the
   human check once. Then ask it for one subject line to prove it works.
8. **Sync** — put the desktop and the token into her app's `sync.json` (or run `sync/set_sync.py`), start
   the server on the laptop, then open her app. Ask it to sync. It should report what moved.

## Prove it before you leave

- [ ] A message gets a real reply
- [ ] The persona chip shows **her** assistant's name, not a default
- [ ] Memory: ask her assistant something only her own memory knows. If it answers, the memory file
      landed; if not, it did not — check `memory/MEMORY.md` before you go
- [ ] Mail returns a real subject line, if mail was set up
- [ ] Sync: edit a line on the laptop, sync on the phone, confirm the line appears

## Leave behind

- [ ] The PDF in her Downloads, and a note of where it is
- [ ] The laptop server left running, or a shortcut on her desktop to start it
- [ ] Nothing with a credential written on paper

## If something fails, in order of likelihood

| Symptom | Cause | Fix |
|---|---|---|
| "App not installed" | an older copy is present | uninstall the old one, install again |
| Installs, opens, will not answer | no model service | step 6 |
| Forgets between visits | battery optimisation | step 5 |
| Memory is empty | the build carried no memory files | check `memory/` in the app's state directory |
| Sync says not configured | `sync.json` missing or malformed | `sync/set_sync.py --check` |
| Sync reaches nothing | phone and laptop on different networks, or firewall | same Wi-Fi; allow Python on private networks |
