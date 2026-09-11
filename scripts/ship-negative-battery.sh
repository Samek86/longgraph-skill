#!/usr/bin/env bash
# Run the Ship-S public-claim meta-test and the S3 negative battery.
# No network. No cloud. Exits non-zero on fail.
#
# Usage:
#   ./scripts/ship-negative-battery.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/runner"

python -m pytest \
  tests/test_public_claims.py::test_public_claims_mapped_tests_exist \
  tests/test_phase1a.py::test_write_set_cannot_escape_workspace \
  tests/test_phase1a.py::test_executor_cannot_clobber_ledger_via_relpath \
  tests/test_contract_holes.py::test_empty_verify_fails_no_close \
  tests/test_contract_holes.py::test_na_verify_skips_gate_and_close \
  tests/test_contract_holes.py::test_blocked_on_skips_executor_until_findings \
  tests/test_contract_holes.py::test_owner_blocked_skips_write_set_and_close \
  tests/test_phase1a.py::test_max_rounds_budget \
  tests/test_contract_holes.py::test_prompt_only_host_never_closes \
  tests/test_contract_holes.py::test_dual_timer_host_never_closes \
  tests/test_phase1c.py::test_dual_timer_stays_deleted_after_terminal \
  tests/test_resume.py::test_verify_green_crash_resumes_verify_only \
  tests/test_gates.py::test_subprocess_verify_red_blocks_close \
  tests/test_gates.py::test_cli_default_gate_is_fail_closed
