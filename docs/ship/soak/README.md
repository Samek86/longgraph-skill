# Soak evidence templates

Committed templates for Ship-S1. **Live** soak output belongs under
`.longgraph-ship/soak/<run-id>/` (gitignored). Do not check in large run trees.

- Protocol: [`../SOAK.md`](../SOAK.md)
- Field list: [`EVIDENCE_TEMPLATE.md`](EVIDENCE_TEMPLATE.md)
- Driver: [`../../../scripts/ship-soak.sh`](../../../scripts/ship-soak.sh)

A live directory is created on each harness run and always includes
`SUMMARY.md` and `summary.json`.
