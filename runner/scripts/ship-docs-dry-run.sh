#!/usr/bin/env bash
# Ship-S4 — fresh-venv proof that README mock + prompt-only paths work.
# Copies add-tests-to-cli (never mutates committed fixtures). Exit 0 only
# when both CLI paths behave as documented.
#
# Usage (from anywhere):
#   bash runner/scripts/ship-docs-dry-run.sh
#   bash runner/scripts/ship-docs-dry-run.sh --no-venv   # use current python
#
# See docs/ship/DOCS-DRY-RUN.md.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNNER="${ROOT}/runner"
FIXTURE="${RUNNER}/tests/fixtures/add-tests-to-cli"

USE_VENV=1
if [[ "${1:-}" == "--no-venv" ]]; then
  USE_VENV=0
fi

if [[ ! -d "${FIXTURE}" ]]; then
  echo "ship-docs-dry-run: missing fixture ${FIXTURE}" >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "ship-docs-dry-run: python3 or python is required" >&2
  exit 2
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/longgraph-docs-dry-run.XXXXXX")"
cleanup() { rm -rf "${WORK}"; }
trap cleanup EXIT

VENV_KIND=""
if [[ "${USE_VENV}" -eq 1 ]]; then
  if "${PY}" -m venv "${WORK}/venv" >/dev/null 2>&1; then
    VENV_KIND="venv"
  else
    rm -rf "${WORK}/venv"
    if "${PY}" -m virtualenv "${WORK}/venv" >/dev/null 2>&1; then
      VENV_KIND="virtualenv"
    else
      echo "ship-docs-dry-run: python -m venv failed (ensurepip missing?); using current interpreter" >&2
      USE_VENV=0
    fi
  fi
fi

if [[ "${USE_VENV}" -eq 1 ]]; then
  # shellcheck disable=SC1091
  source "${WORK}/venv/bin/activate"
  PY=python
  "${PY}" -m pip install -q -U pip
  "${PY}" -m pip install -q -e "${RUNNER}[dev]"
fi

cd "${RUNNER}"
INSTALL_CMD='python -m pip install -e ".[dev]"'
if [[ "${USE_VENV}" -eq 1 ]]; then
  INSTALL_CMD="python -m ${VENV_KIND} <tmp>/venv && source <tmp>/venv/bin/activate && ${INSTALL_CMD}"
fi

export LONGGRAPH_DOCS_DRY_RUN_WORK="${WORK}"
export LONGGRAPH_DOCS_DRY_RUN_INSTALL="${INSTALL_CMD}"
exec "${PY}" "${RUNNER}/scripts/ship_docs_dry_run.py"
