#!/usr/bin/env bash
# Run the GitHub workflow's environment on this machine, before GitHub ever sees it.
#
# Why: `ci/ci.sh` is the gate, but the gate is not the whole story. A workflow fails on the *machine*
# — a package that isn't installed, a browser at a different path, a Python that is a different minor.
# This builds the runner image from `ci/Dockerfile.runner`, runs the gate inside it against the working
# tree, and reports what the runner would report.
#
#   ./ci/local-runner.sh            # build the image (cached after the first time) and run the gate
#   ./ci/local-runner.sh --shell    # drop into the image with the tree mounted
#   RUNTIME=podman ./ci/local-runner.sh
#
# The tree is mounted read-write because the gate rebuilds the guide and then checks for drift: a
# read-only mount would make that check fail for the wrong reason.
set -euo pipefail

cd "$(dirname "$0")/.."
RUNTIME="${RUNTIME:-$(command -v docker || command -v podman || true)}"
if [ -z "$RUNTIME" ]; then
  echo "no container runtime: install docker or podman, or run ./ci/ci.sh directly" >&2
  exit 2
fi

IMAGE="quixidesk-ci:local"

echo "== building the runner image ($RUNTIME)"
"$RUNTIME" build -f ci/Dockerfile.runner -t "$IMAGE" . >"${TMPDIR:-/tmp}/quixidesk-ci-build.log" 2>&1 \
  || { tail -20 "${TMPDIR:-/tmp}/quixidesk-ci-build.log"; exit 1; }

if [ "${1:-}" = "--shell" ]; then
  exec "$RUNTIME" run --rm -it -v "$PWD":/work -w /work "$IMAGE" bash
fi

echo "== running the gate inside the runner"
# Run as the invoking user, not as root. Chrome refuses to start as root without --no-sandbox, and
# passing that flag would make this container *less* like the GitHub runner than no container at all:
# a real runner is a normal user, and the point of this script is to reproduce that, not to paper
# over the difference. It also keeps the guide rebuild able to write into the mounted tree.
# --no-sandbox and a real /dev/shm are container concessions, not workflow ones: GitHub's runners
# have user namespaces and 1 GB of shared memory, an unprivileged container here has neither. They
# are passed in as Chrome flags through the environment so the workflow is untouched.
"$RUNTIME" run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -e CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage" \
  --shm-size=1g \
  -v "$PWD":/work -w /work "$IMAGE" ./ci/ci.sh
