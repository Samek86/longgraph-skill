# Fork Attribution

This repository is an **enhanced fork** of [levi-qiao/longgraph-skill](https://github.com/levi-qiao/longgraph-skill), maintained by [Samek86](https://github.com/Samek86).

## Upstream

- **Original Author**: [levi-qiao](https://github.com/levi-qiao)
- **Original Repository**: https://github.com/levi-qiao/longgraph-skill
- **License**: MIT License (see [LICENSE](LICENSE))

## Enhancements in This Fork

This fork preserves the original MIT license and upstream copyright while adding practical reinforcements for production long-horizon agent work:

### 1. **Trilingual Documentation**
- Full Japanese (`README.ja.md`) and Korean (`README.ko.md`) translations alongside the original English README
- Cross-linked at the top of each README for easy navigation

### 2. **Observability — Deep status.json Wiring**
- Machine-readable run status sidecar (`.longgraph/<run>/status.json`)
- **Compiler auto-generates** initial status.json for every new run
- **Templates instruct nodes** how/when to update fields (phase, progress, heartbeats, terminal state)
- Helper script (`scripts/update-status.sh`) for manual status field updates
- Schema and integration documentation in `docs/observability/status-schema.md`
- Live run artifacts emit real-time progress (not docs-only)

### 3. **Scout on Preset Hot Path — Auto-Brief Lifecycle**
- **Scout node becomes first-class** for focused presets (loop-research, loop-deliver, loop-converge)
- **Compiler auto-emits** Scout brief + findings directory when preset needs off-critical-path research
- Full lifecycle documentation (`skills/loop-graph/docs/scout-lifecycle.md`)
- Templates include Scout consumption (executor) and audit (supervisor) protocols
- Read-on-reference findings protocol (O(active briefs), not O(total briefs))

### 4. **Secret Scrubbing**
- Local secret-scanning script (`scripts/scrub-longgraph-secrets.sh`)
- Scans `.longgraph/` for common secret patterns before sharing or committing
- Fail-closed design with no network calls

### 5. **CI Validation**
- GitHub Actions workflow validating:
  - SKILL.md frontmatter presence
  - README cross-linking (EN/JA/KO)
  - Template structure checks
  - status.json wiring presence in templates
  - Scout lifecycle documentation completeness
- Runs on every PR to catch regressions early

## Compatibility with Upstream

All enhancements are **additive**. The core loop-graph design remains unchanged:
- Same executor + supervisor + ledger architecture
- Same no-wake-edge invariant
- Same single-writer edge discipline
- Same host portability (Claude Code · Cursor · Codex · Grok Build)

## Contributing

For contributions specific to this fork's enhancements, open issues or PRs in this repository. For core loop-graph methodology or baseline features, consider contributing to the [upstream repository](https://github.com/levi-qiao/longgraph-skill) first.

## Credits

This fork exists thanks to:
- **levi-qiao** and the longgraph-skill community for the foundational methodology
- Feedback from production users requesting observability and secret-safety tooling
- The multilingual open-source community

---

**Maintained by**: [Samek86](https://github.com/Samek86)  
**Upstream**: [levi-qiao/longgraph-skill](https://github.com/levi-qiao/longgraph-skill)  
**License**: [MIT](LICENSE) © 2026 levi-qiao
