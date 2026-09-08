# Run Status Schema

longgraph runs can emit a machine-readable `status.json` file for monitoring, dashboards, and CI integration.

## Location

`.longgraph/<date-slug>/status.json`

Each run writes its own status file in its run directory.

## Schema

```json
{
  "version": "1.0",
  "runId": "<date-slug>",
  "createdAt": "2026-09-08T10:00:00Z",
  "updatedAt": "2026-09-08T12:30:00Z",
  "status": "running",
  "phase": "executing",
  "progress": {
    "completedRounds": 5,
    "totalItems": 12,
    "completedItems": 4,
    "blockedItems": 1,
    "currentItem": "implement-auth-middleware"
  },
  "nodes": {
    "executor": {
      "lastHeartbeat": "2026-09-08T12:30:00Z",
      "currentRound": 5,
      "status": "active"
    },
    "supervisor": {
      "lastHeartbeat": "2026-09-08T12:25:00Z",
      "lastReview": "2026-09-08T12:20:00Z",
      "status": "active"
    }
  },
  "metadata": {
    "host": "cursor",
    "goal": "Add authentication middleware with tests",
    "owner": "dev-team",
    "tags": ["auth", "security"]
  }
}
```

## Field Definitions

### Top-Level

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version (currently `"1.0"`) |
| `runId` | string | Run identifier (date-slug) |
| `createdAt` | string (ISO 8601) | When the run started |
| `updatedAt` | string (ISO 8601) | Last status update timestamp |
| `status` | enum | Overall run status (see below) |
| `phase` | enum | Current execution phase (see below) |

### Status Values

- `"initializing"` — Run setup in progress
- `"running"` — Actively executing
- `"paused"` — Temporarily paused (manual or gate-wait)
- `"completed"` — All items done, gates passed
- `"failed"` — Unrecoverable failure
- `"cancelled"` — Owner-cancelled

### Phase Values

- `"setup"` — Initial compilation and preparation
- `"executing"` — Executor processing ledger items
- `"reviewing"` — Supervisor verifying work
- `"blocked"` — Waiting for owner decision or gate
- `"converging"` — Forced convergence or cleanup
- `"done"` — Final handoff complete

### Progress

| Field | Type | Description |
|-------|------|-------------|
| `completedRounds` | number | Total rounds executed |
| `totalItems` | number | Total ledger items |
| `completedItems` | number | Items marked done |
| `blockedItems` | number | Items blocked/parked |
| `currentItem` | string | ID of item being processed |

### Nodes

Each node (executor, supervisor, scout) can report:

| Field | Type | Description |
|-------|------|-------------|
| `lastHeartbeat` | string (ISO 8601) | Most recent activity |
| `status` | enum | `"active"`, `"idle"`, `"stopped"`, `"error"` |

## Usage

### Emitting Status (Optional)

Add this to your executor or supervisor template at natural checkpoints:

```bash
# Update status after completing a round
cat > .longgraph/${RUN_DIR}/status.json <<EOF
{
  "version": "1.0",
  "runId": "${RUN_DIR}",
  "updatedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "running",
  "phase": "executing",
  "progress": {
    "completedRounds": ${ROUND_NUM},
    "currentItem": "${CURRENT_ITEM}"
  }
}
EOF
```

Or from Python:

```python
import json
from datetime import datetime, timezone

def update_status(run_dir, status, phase, progress):
    status_file = f".longgraph/{run_dir}/status.json"
    with open(status_file, "w") as f:
        json.dump({
            "version": "1.0",
            "runId": run_dir,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "phase": phase,
            "progress": progress
        }, f, indent=2)
```

### Reading Status

Monitor all runs:

```bash
# List all active runs
find .longgraph -name status.json -exec jq -r \
  'select(.status == "running") | "\(.runId): \(.progress.completedItems)/\(.progress.totalItems)"' \
  {} \;

# Check for stale runs (no heartbeat in 1 hour)
find .longgraph -name status.json -mmin +60 -exec cat {} \;
```

Integrate with CI:

```yaml
# GitHub Actions example
- name: Check longgraph status
  run: |
    STATUS=$(jq -r '.status' .longgraph/*/status.json)
    if [ "$STATUS" = "failed" ]; then
      echo "Run failed"
      exit 1
    fi
```

## Best Practices

1. **Update at round boundaries** — Not mid-work; keep I/O minimal
2. **Atomic writes** — Write to temp file, then rename
3. **Graceful degradation** — Missing status.json is not an error
4. **No secrets** — Never include tokens, credentials, or PII
5. **Timezone-aware** — Always use UTC (ISO 8601 with `Z`)

## Integration with Templates

The loop-graph compiler can optionally inject status hooks into generated executor/supervisor templates. See `skills/loop-graph/docs/preset-contract.md` for the status-reporting extension point.

## Backward Compatibility

`status.json` is entirely optional. Existing runs without it continue working normally. Monitoring tools should gracefully handle:
- Missing files
- Partial schemas (older versions)
- Stale timestamps

---

For questions or schema evolution proposals, open an issue at https://github.com/Samek86/longgraph-skill/issues.
