#!/usr/bin/env bash
#
# update-status.sh — helper script to update status.json fields
#
# Usage:
#   ./scripts/update-status.sh <run-dir> [options]
#
# Options:
#   --status <value>           Set overall status (initializing/running/paused/completed/failed/cancelled)
#   --phase <value>            Set phase (setup/executing/reviewing/blocked/converging/done)
#   --rounds <number>          Set completed rounds count
#   --current-item <id>        Set current item ID
#   --executor-status <value>  Set executor node status (idle/active/stopped/error)
#   --supervisor-status <value> Set supervisor node status (idle/active/stopped/error)
#
# Examples:
#   # Update after completing round 5
#   ./scripts/update-status.sh .longgraph/2026-09-08-deliver \
#     --rounds 5 --current-item "implement-auth"
#
#   # Mark run as completed
#   ./scripts/update-status.sh .longgraph/2026-09-08-deliver \
#     --status completed --phase done \
#     --executor-status stopped --supervisor-status stopped

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help text
show_help() {
  cat << EOF
update-status.sh — Update status.json for a longgraph run

Usage:
  $(basename "$0") <run-dir> [options]

Arguments:
  run-dir                      Path to run directory (e.g. .longgraph/2026-09-08-deliver)

Options:
  --status <value>             Set overall status
                               Values: initializing, running, paused, completed, failed, cancelled
  --phase <value>              Set execution phase
                               Values: setup, executing, reviewing, blocked, converging, done
  --rounds <number>            Set completed rounds count
  --current-item <id>          Set current item ID (or "null" to clear)
  --executor-status <value>    Set executor node status
                               Values: idle, active, stopped, error
  --supervisor-status <value>  Set supervisor node status
                               Values: idle, active, stopped, error
  -h, --help                   Show this help

Examples:
  # Update after round completion
  $(basename "$0") .longgraph/2026-09-08-deliver --rounds 5 --current-item "auth-impl"

  # Mark terminal state
  $(basename "$0") .longgraph/2026-09-08-deliver --status completed --phase done

Exit codes:
  0   Success
  1   Invalid arguments or run directory not found
  2   jq not available
EOF
}

# Check dependencies
if ! command -v jq &> /dev/null; then
  echo -e "${RED}Error: jq is required but not installed${NC}" >&2
  echo "Install: apt-get install jq  # Debian/Ubuntu" >&2
  echo "         brew install jq      # macOS" >&2
  exit 2
fi

# Parse arguments
if [ $# -lt 1 ]; then
  show_help
  exit 1
fi

RUN_DIR="$1"
shift

if [ "$RUN_DIR" = "-h" ] || [ "$RUN_DIR" = "--help" ]; then
  show_help
  exit 0
fi

# Validate run directory
if [ ! -d "$RUN_DIR" ]; then
  echo -e "${RED}Error: Run directory not found: $RUN_DIR${NC}" >&2
  exit 1
fi

STATUS_FILE="$RUN_DIR/status.json"

if [ ! -f "$STATUS_FILE" ]; then
  echo -e "${YELLOW}Warning: status.json not found in $RUN_DIR${NC}" >&2
  echo "This run may not have status.json enabled." >&2
  exit 1
fi

# Build jq filter from options
JQ_FILTER=".updatedAt = \$now"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

while [ $# -gt 0 ]; do
  case "$1" in
    --status)
      shift
      case "$1" in
        initializing|running|paused|completed|failed|cancelled)
          JQ_FILTER="$JQ_FILTER | .status = \"$1\""
          ;;
        *)
          echo -e "${RED}Error: Invalid status value: $1${NC}" >&2
          echo "Valid: initializing, running, paused, completed, failed, cancelled" >&2
          exit 1
          ;;
      esac
      shift
      ;;
    --phase)
      shift
      case "$1" in
        setup|executing|reviewing|blocked|converging|done)
          JQ_FILTER="$JQ_FILTER | .phase = \"$1\""
          ;;
        *)
          echo -e "${RED}Error: Invalid phase value: $1${NC}" >&2
          echo "Valid: setup, executing, reviewing, blocked, converging, done" >&2
          exit 1
          ;;
      esac
      shift
      ;;
    --rounds)
      shift
      if ! [[ "$1" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: --rounds must be a number: $1${NC}" >&2
        exit 1
      fi
      JQ_FILTER="$JQ_FILTER | .progress.completedRounds = $1"
      shift
      ;;
    --current-item)
      shift
      if [ "$1" = "null" ]; then
        JQ_FILTER="$JQ_FILTER | .progress.currentItem = null"
      else
        JQ_FILTER="$JQ_FILTER | .progress.currentItem = \"$1\""
      fi
      shift
      ;;
    --executor-status)
      shift
      case "$1" in
        idle|active|stopped|error)
          JQ_FILTER="$JQ_FILTER | .nodes.executor.status = \"$1\""
          JQ_FILTER="$JQ_FILTER | .nodes.executor.lastHeartbeat = \$now"
          ;;
        *)
          echo -e "${RED}Error: Invalid executor-status: $1${NC}" >&2
          echo "Valid: idle, active, stopped, error" >&2
          exit 1
          ;;
      esac
      shift
      ;;
    --supervisor-status)
      shift
      case "$1" in
        idle|active|stopped|error)
          JQ_FILTER="$JQ_FILTER | .nodes.supervisor.status = \"$1\""
          JQ_FILTER="$JQ_FILTER | .nodes.supervisor.lastHeartbeat = \$now"
          ;;
        *)
          echo -e "${RED}Error: Invalid supervisor-status: $1${NC}" >&2
          echo "Valid: idle, active, stopped, error" >&2
          exit 1
          ;;
      esac
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option: $1${NC}" >&2
      show_help
      exit 1
      ;;
  esac
done

# Apply updates atomically
TEMP_FILE="$STATUS_FILE.tmp.$$"
trap "rm -f '$TEMP_FILE'" EXIT

if ! jq "$JQ_FILTER" --arg now "$NOW" "$STATUS_FILE" > "$TEMP_FILE"; then
  echo -e "${RED}Error: jq filter failed${NC}" >&2
  exit 1
fi

if ! mv "$TEMP_FILE" "$STATUS_FILE"; then
  echo -e "${RED}Error: Failed to write $STATUS_FILE${NC}" >&2
  exit 1
fi

echo -e "${GREEN}✅ Updated $STATUS_FILE${NC}"
echo "Timestamp: $NOW"

# Show updated fields (optional, for verification)
if [ -t 1 ]; then
  echo ""
  echo "Current status:"
  jq -C '{ status, phase, progress: { completedRounds, currentItem }, nodes: { executor: .nodes.executor.status, supervisor: .nodes.supervisor.status }}' "$STATUS_FILE"
fi
