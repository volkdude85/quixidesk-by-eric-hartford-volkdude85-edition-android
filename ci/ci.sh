#!/usr/bin/env bash
# The gate. Run this before every push; CI runs the same file, so a green run here means a green run
# there and there is no second, secret definition of "passing".
#
#   ./ci/ci.sh          full
#   ./ci/ci.sh --fast   skip the guide rebuild (a minute) when only prose changed
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
ROOT=$PWD
FAST=0
[ "${1:-}" = "--fast" ] && FAST=1

PY=/usr/bin/python3
fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   ok   %s\n' "$1"; }
bad()  { printf '   FAIL %s\n' "$1"; fail=1; }

# ── 1. Python parses ────────────────────────────────────────────────────────────
step "python syntax"
while IFS= read -r f; do
  if $PY -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" 2>/dev/null; then
    ok "$f"
  else
    bad "$f"
  fi
done < <(find sync tools -name '*.py' | sort)

# ── 2. Shell parses ────────────────────────────────────────────────────────────
step "shell syntax"
while IFS= read -r f; do
  if bash -n "$f" 2>/dev/null; then ok "$f"; else bad "$f"; fi
done < <(find . -name '*.sh' -not -path './.git/*' | sort)

# ── 3. The sync protocol's own tests ───────────────────────────────────────────
# The code that decides what may cross the wire, and what happens when two machines disagree, is the
# part of this project most able to lose someone's data. It gets real tests, on a real temp directory,
# with no mocks: whitelist refusals, traversal, conflict copies, revision rules, streaming, short
# bodies, and absurd content lengths.
step "sync route tests"
if $PY -m unittest discover -s tests -q 2>/tmp/ci-tests.log; then
  ok "$(grep -oE 'Ran [0-9]+ tests' /tmp/ci-tests.log | tail -1)"
else
  bad "sync route tests failed"
  tail -20 /tmp/ci-tests.log
fi

# ── 4. Documentation links resolve ─────────────────────────────────────────────
step "documentation links"
if $PY tools/check_links.py; then ok "every internal link resolves"; else bad "a link points at nothing"; fi

# ── 5. No identifying material ─────────────────────────────────────────────────
step "identifier scan"
if $PY tools/doxcheck.py . ; then
  ok "clean"
else
  bad "the package carries identifying material (see above)"
fi

# ── 6. The guide still builds, and its contents page still tells the truth ─────
# Skipped with --fast. The build re-measures every page number and fails on drift, so this is a real
# check rather than "the command exited 0".
if [ "$FAST" = "0" ]; then
  step "guide rebuild"
  before=$(sha256sum docs/guide/QuixiDesk-Android-Guide.pdf 2>/dev/null | cut -d' ' -f1)
  if $PY tools/build_guide.py > /tmp/ci-guide.log 2>&1; then
    if grep -q 'drift after stamping: none' /tmp/ci-guide.log; then
      ok "renders, contents page measured, no drift"
    else
      bad "contents page numbers shifted between passes"
      grep 'drift' /tmp/ci-guide.log || true
    fi
  else
    bad "guide did not build"
    tail -5 /tmp/ci-guide.log || true
  fi
  after=$(sha256sum docs/guide/QuixiDesk-Android-Guide.pdf 2>/dev/null | cut -d' ' -f1)
  [ "$before" = "$after" ] && ok "PDF byte-identical to the committed one" \
                           || printf '   note the PDF changed this run (fine if the sources did)\n'
fi

# ── 7. Figures exist and are not empty ──────────────────────────────────────────
step "figures"
missing=0
for img in $(grep -o 'src="figures/[^"]*"' docs/guide/guide.html | sed 's/src="//;s/"//'); do
  if [ -s "docs/guide/$img" ]; then
    :
  else
    bad "docs/guide/$img missing or empty"
    missing=1
  fi
done
[ "$missing" = "0" ] && ok "every figure referenced by the guide is present"

# ── 8. Screenshots referenced by the README exist ──────────────────────────────
step "screenshots"
sm=0
for img in $(grep -o 'docs/screenshots/[a-z]*\.png' README.md | sort -u); do
  [ -s "$img" ] || { bad "$img missing or empty"; sm=1; }
done
[ "$sm" = "0" ] && ok "every README image is present"

printf '\n'
if [ "$fail" = "0" ]; then
  printf 'CI: PASS\n'
else
  printf 'CI: FAIL\n'
fi
exit $fail
