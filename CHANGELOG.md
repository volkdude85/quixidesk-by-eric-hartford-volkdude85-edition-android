# Changelog

## 0.1.0 — first packaged release

Documentation, sync tooling and the scripts that produce both. No application binary ships here; see
the README for why.

### Guide
- 16-page A4 setup guide covering install, Developer options, USB and wireless debugging, battery
  exemption, model service setup, the one-time mail sign-in, Android Auto, troubleshooting, a Windows
  appendix and how to undo every step.
- Six figures, each a real device screenshot with the target control cut out and boxed. All generated
  by `tools/annotate.py` from `tools/capture.sh` output, so a UI change is two commands to re-shoot.
- Contents page numbers are measured from the rendered PDF, not typed, and re-verified for drift.

### Sync
- `sync/sync_server.py`: desktop half. Pure Python 3, no dependencies. Serves a fixed list of state
  files behind a bearer token; refuses paths outside the list and `../`.
- Phone half lives in the app: manifest compare, newer copy wins, loser preserved as
  `<file>.conflict-<machine>-<timestamp>`, sync on every app open.
- Verified both directions against a real device: `pushed 3 · pulled 1 · errors 0`, then
  `pushed 0 · pulled 0` on the next pass.

### Tooling
- `tools/doxcheck.py`: fails on emails, phone numbers, street addresses, home paths, LAN and Tailscale
  addresses, device serials, IMEI-shaped numbers, keys and password literals.
- `tools/build_guide.py`: renders the PDF and stamps the contents page from measurements.
