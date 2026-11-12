QuixiDesk phone sync — Windows side
===================================

What it is
  One small Python file that lets the phone and this computer exchange the assistant's memory,
  persona and preferences. Neither machine is the master: the newer copy wins, the older one is kept
  beside it, and the two converge the next time they meet.

What you need
  Python 3 (python.org). Nothing else — no Node, no compiler, no service to register.

First time
  1. Edit start-sync-server.cmd and change TOKEN to a long random string. Keep a copy of it.
  2. Double-click start-sync-server.cmd. Leave the window open.
  3. On the phone, put the same address and token in sync.json (see the guide, Appendix C).

What syncs
  memory/MEMORY.md, memory/USER.md, memory/FAMILY-REFERENCE.txt, persona.md, preferences.json
  Nothing else does — sessions, workspace, keys and credentials stay where they are.

When both machines changed the same file
  Nothing is lost. The version that lost is saved next to it, named
  <file>.conflict-<machine>-<time>, and it stays there until someone deletes it.

Firewall
  The first time Windows asks, allow Python on Private networks only. The phone cannot reach this
  computer from a public network, and it should not be able to.
