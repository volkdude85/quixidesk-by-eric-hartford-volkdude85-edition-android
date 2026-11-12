# Contributing

Small project, two rules.

1. **No personal data, ever.** Names, addresses, phone numbers, real e-mail addresses, LAN addresses,
   device serials and keys do not go into commits, screenshots or documentation. `tools/doxcheck.py`
   gates this; run it before opening a pull request.

   ```bash
   /usr/bin/python3 tools/doxcheck.py docs/guide/guide.html docs/guide/QuixiDesk-Android-Guide.pdf
   ```

2. **Regenerate, do not hand-edit.** The figures come from `tools/capture.sh` and `tools/annotate.py`;
   the PDF and its contents page come from `tools/build_guide.py`. Editing the PDF or a screenshot by
   hand means the next regeneration silently undoes it.

Device screenshots should come from a clean device or emulator, cropped to the application surface,
with anything identifying blurred before it is committed.
