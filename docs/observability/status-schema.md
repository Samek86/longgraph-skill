# Run Status Schema

longgraph runs can emit a machine-readable `status.json` file for monitoring, dashboards, and CI integration.

## Location

`.longgraph/<date-slug>/status.json`

Each run writes its own status file in its run directory.

## Authority (runner vs legacy)

- **Runner-managed runs require `status.json`.** The Phase 0/1a runner
  will not start a run directory that lacks the file. See
  [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md) §4 and
  [`docs/runner/AUTHORITY.md`](../runner/AUTHORITY.md).
- **Writes are atomic:** write `status.json.tmp` in the same directory,
  then `mv` / `os.replace` onto `status.json`. Never truncate the live
  file in place.
- **Legacy / skill-hosted runs** (no runner) may still omit the file.
  Monitoring tools should treat a missing file as "not runner-managed",
  not as a hard error, for those runs only.

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
  "ownerEscalation": null,
  "metadata": {
    "host": "cursor",
    "goal": "Add authentication middleware with tests",
    "owner": "dev-team",
    "tags": ["auth", "security"],
    "itemRetries": {},
    "lastAttempt": null
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
| `ownerEscalation` | object or `null` | Outstanding owner choice-card, or `null` |

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

### Metadata

| Field | Type | Description |
|-------|------|-------------|
| `host` | string | Host name (`cursor`, `mock`, …) |
| `goal` | string | Short goal summary |
| `owner` | string | Owner identifier |
| `tags` | string[] | Free-form tags |
| `itemRetries` | object | Map of `item_id` → retry count. Allowed and required for runner-managed runs. |
| `lastAttempt` | object or `null` | Idempotency key + phase (`write` / `verify` / `verify_green` / `closed`) |

### Nodes

Each node (executor, supervisor, scout) can report:

| Field | Type | Description |
|-------|------|-------------|
| `lastHeartbeat` | string (ISO 8601) | Most recent activity |
| `status` | enum | `"active"`, `"idle"`, `"stopped"`, `"error"` |

## Usage

### Emitting Status

**Runner-managed runs** must use the runner's atomic writer (tmp + `os.replace`).
Do not invent a second writer.

#### Legacy (skill-hosted / manual only)

The following `cat >` snippet is **legacy**. It is not atomic and must not
be used by the runner. Kept so existing host checklists still parse.

```bash
# LEGACY — not atomic; do not use for runner-managed runs
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

Atomic form (required for the runner; recommended everywhere else):

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path

def update_status(status_path, payload):
    path = Path(status_path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
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
2. **Atomic writes** — Write to `status.json.tmp`, then `mv` / `os.replace`. Required for runner-managed runs.
3. **Graceful degradation** — Missing `status.json` is not an error for **legacy skill-hosted** runs. It **is** an error for the runner.
4. **No secrets** — Never include tokens, credentials, or PII
5. **Timezone-aware** — Always use UTC (ISO 8601 with `Z`)
6. **`completed` implies terminal ledger** — Do not persist `status: "completed"` while `Run status` is still `active`.

## Integration with Templates

The loop-graph compiler can optionally inject status hooks into generated executor/supervisor templates. See `skills/loop-graph/docs/preset-contract.md` for the status-reporting extension point.

## Backward Compatibility

For **legacy skill-hosted** runs, `status.json` remains optional. Monitoring
tools should gracefully handle missing files, partial schemas, and stale
timestamps on those runs.

For **runner-managed** runs, `status.json` is required, must include
`ownerEscalation` (nullable) and may include `metadata.itemRetries`, and
must be written atomically.

---

For questions or schema evolution proposals, open an issue at https://github.com/Samek86/longgraph-skill/issues.
