# longgraph runner (Phase 1a MockHost)

Engine for compiled run directories. The skill library under `skills/` is
policy only — this package never loads it.

Authority: [`docs/runner/AUTHORITY.md`](../docs/runner/AUTHORITY.md).

```bash
cd runner
python -m pip install -e ".[dev]"
python -m pytest
longgraph run|status|stop <run_dir>
```

Host is MockHost (no model). Close is gate re-pass only.
