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

### 2. **Observability**
- Machine-readable run status sidecar (`.longgraph/<run>/status.json`)
- Schema and integration documentation in `docs/observability/`
- Optional but documented for production monitoring

### 3. **Secret Scrubbing**
- Local secret-scanning script (`scripts/scrub-longgraph-secrets.sh`)
- Scans `.longgraph/` for common secret patterns before sharing or committing
- Fail-closed design with no network calls

### 4. **CI Validation**
- GitHub Actions workflow validating:
  - SKILL.md frontmatter presence
  - README cross-linking (EN/JA/KO)
  - Basic template structure checks
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
