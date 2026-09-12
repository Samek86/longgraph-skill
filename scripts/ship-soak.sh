#!/usr/bin/env bash
# ship-soak.sh — Ship-S1 multi-fixture soak harness (not a product runtime).
#
# Usage:
#   ./scripts/ship-soak.sh [--rounds N] [--host mock|prompt-only] [--out DIR] [fixture ...]
#
# Defaults: --rounds 5 (CI/smoke), --host mock, the three runner/tests/fixtures/.
# Production D2 evidence: --rounds 50 (N>=50) or a >=24h operator wall-clock run.
# See docs/ship/SOAK.md.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/runner${PYTHONPATH:+:$PYTHONPATH}"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "ship-soak: python3 or python is required" >&2
  exit 2
fi

exec "$PY" "${ROOT}/scripts/ship_soak.py" "$@"
