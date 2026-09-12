# Soak evidence templates

Committed templates for Ship-S1. Scratch harness output belongs under
`.longgraph-ship/soak/<run-id>/` (gitignored). Do not check in isolated
work trees.

Tip production **mock N=50** evidence is in-repo:

- [`tip-5de40a9-n50-mock/`](tip-5de40a9-n50-mock/) — tip `5de40a9`,
  `host=mock`, N=50, three golden fixtures. Compact traces only.

Live DualTimer multi-day soak remains owner-only.

- Protocol: [`../SOAK.md`](../SOAK.md)
- Field list: [`EVIDENCE_TEMPLATE.md`](EVIDENCE_TEMPLATE.md)
- Driver: [`../../../scripts/ship-soak.sh`](../../../scripts/ship-soak.sh)

A harness run always writes `SUMMARY.md` and `summary.json`.
