<div align="center">

# longgraph

**Long-horizon agent skill for Claude Code, Cursor, Codex & Grok Build.**

Stop agent drift with a durable ledger, a clean-context supervisor, and verified gates.
Queue many long tasks in one loop — even unrelated ones — and keep going after a host switch
by re-sending the same prompt against the files.

Design once → compile a durable loop-graph → verify all the way to done.

[![GitHub stars](https://img.shields.io/github/stars/levi-qiao/longgraph-skill?style=flat-square&color=6C63FF)](https://github.com/levi-qiao/longgraph-skill/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-14B8A6?style=flat-square)](LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-22C55E?style=flat-square)](CONTRIBUTING.md)
![Hosts: Claude Code · Cursor · Codex · Grok Build](https://img.shields.io/badge/Hosts-Claude%20Code%20·%20Cursor%20·%20Codex%20·%20Grok%20Build-111827?style=flat-square)
![Type: agent skill · prompt library](https://img.shields.io/badge/Type-agent%20skill%20·%20prompt%20library-0EA5E9?style=flat-square)

English · [日本語](README.ja.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

</div>

<img alt="Executor and clean-context supervisor loops running side by side" src="assets/graph.png" width="100%" />

## 📌 About This Fork

This is an **enhanced fork** of [levi-qiao/longgraph-skill](https://github.com/levi-qiao/longgraph-skill), maintained by [Samek86](https://github.com/Samek86).

### 🎯 Added Features

- **📚 Trilingual Documentation**: Complete READMEs in English, Japanese, and Korean
- **📊 Deep status.json Wiring**: Live run artifacts emit machine-readable progress (`status.json`) — nodes update phase, rounds, heartbeats automatically; helper script + CI validation included
- **🔍 Scout Auto-Brief Lifecycle**: Scout node on preset hot path — compiler auto-emits Scout brief + findings protocol for off-critical-path research (loop-research / loop-deliver / loop-converge)
- **🔒 Secret Scrubbing**: Local script to scan for secrets before committing
- **✅ CI Validation**: Automated structure and link validation via GitHub Actions

> **Upstream Compatibility**: All enhancements are additive. The core loop-graph design remains unchanged.
> See [FORK.md](FORK.md) for details.

---

**longgraph** (`longgraph-skill`) is a curated **agent skill** and cross-host
**prompt library** for **long-running / long-horizon** agent work — multi-hour
coding, multi-milestone migrations, a **queue of long tasks in one loop** (they
need not be related), and anything that outlives one context window. It is
**graph engineering for agents**: specialized roles (executor · supervisor ·
scout) connected through durable, inspectable files — not another orchestration
runtime. Because the scoreboard lives on disk, you can **change hosts mid-run**:
open the same workspace, re-send the frozen node prompt, and continue.

> **One durable graph, portable across hosts.** For a simple self-contained goal,
> use the host's normal task or goal directly; longgraph starts where durable graph
> structure adds value.

## Evidence

These are not one-shot demos. longgraph is a **Markdown skill / prompt library**
(not an orchestration runtime). The table mixes **checkable public Git**, a
**function-only redacted multi-day pattern**, and **synthetic pedagogy**.

| Case | What a reader can verify | Kind |
| --- | --- | --- |
| [**Self-iteration of this skill**](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md) | **87** public commits across **~14 calendar days** (2026-07-19 → 2026-08-02), **74** files, method rules written back into the library (no wake edge, gate-wait backlog, blocked≠parked, bounded live edges, authoring≠runtime) | Public Git facts — fixed anchor `6efcb7f` |
| [**Multi-day control-plane pattern**](skills/loop-graph/examples/redacted-multiday-control-plane/README.md) | Multi-day wall-clock, tens of rounds, many directives: durable ledger, clean-context supervisor overturns self-reported evidence, non-skippable gates, blocked-work lane, owner A/B/C — **functions only**, no private payload | Redacted real-run pattern |
| [**migrate-blob-storage**](skills/loop-graph/examples/migrate-blob-storage/README.md) | Multi-milestone ledger: pilot → cohort, forced convergence, supervisor overturns self-reported evidence, non-skippable gate + blocked-work lane | Synthetic pedagogy (fictional app) |
| [**add-tests-to-cli**](skills/loop-graph/examples/add-tests-to-cli/README.md) | Smallest full run: three rounds, register-then-defer, clean-context supervisor intent | Synthetic pedagogy (fictional CLI) |

**How to read the clock.** The self-iteration window’s ~14 days / ~340 hours is
**project wall-clock** (first public commit → frozen anchor), not continuous model
execution and not a claim of unattended production autonomy. Re-check Git with the
commands in the [self-iteration case](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md).
The redacted multi-day card uses **coarse buckets only** and is **not** private-Git
re-checkable — see its evidence boundary.

Publication rules for future cases:
[public / private boundary](docs/public-private-boundary.md).

## When to use this

Reach for longgraph when you need any of:

- A **long-horizon agent** that keeps working after context compaction / session resets
- A **durable task ledger** (single scoreboard) instead of chat-memory progress
- **Several long tasks in one loop** — a continuous queue, even when items are unrelated
- **Host-portable continuity** — switch Claude Code ↔ Cursor ↔ Codex ↔ Grok Build mid-run by re-sending the prompt against the same files
- An independent **clean-context supervisor** — not the same agent grading itself
- **Verified done**: acceptance gates re-run against real output, not self-reported “done”
- Multi-milestone work with **non-skippable gates** and explicit owner red lines
- A **Markdown skill / prompt library** that works across **Claude Code · Cursor · Codex · Grok Build**

### When *not* to use this

- One-shot edits, small PR-sized tasks, or anything that fits a single clean session
- You want a **runtime framework** (LangGraph, CrewAI, AutoGen, custom agent server)
- You only need a single short prompt with no ledger, gates, or independent review

### How it compares

| Approach | Runtime / server? | Independent verifier | Durable scoreboard | Multi-task queue + mid-run host switch |
| --- | --- | --- | --- | --- |
| LangGraph / CrewAI / AutoGen | Yes | You build it | Usually yes | Framework-bound; often one deployment stack |
| One mega-prompt / single skill | No | No (self-check) | Weak (chat memory) | Weak — progress dies with the session |
| **longgraph (this fork)** | **Default: runner CLI** (`longgraph run`); skill compile ≠ engine | **Yes (supervisor node)** | **Yes (`ledger.md`)** | **Yes — files are the run; AI runs the CLI** |

Also called / related searches: *longgraph skill*, *long-horizon agent skill*,
*long-running agent skill*, *prevent agent drift*, *multi-task agent loop*,
*switch AI coding host mid-task*, *Claude Code multi-agent supervisor*,
*Grok Build agent loop*, *agent ledger*, *loop-graph*, *graph engineering for
agents*, *clean-context review*.

## Why longgraph

Long-running agents tend to drift in predictable ways: scope expands, “done”
becomes self-reported, tests stop proving the real path, and early decisions
disappear from context. longgraph moves the safeguards outside the model’s memory:

- **Verified, not merely written** — acceptance gates are rerun against real output.
- **Durable state** — the ledger survives context loss and remains the single scoreboard.
- **Many long tasks, one loop** — the ledger is a continuous queue; items can be
  independent (migrations, test debt, docs, gates) without forcing one mega-goal.
- **Host-portable** — progress is files under `.longgraph/<date-slug>/`, not chat
  history. Point another host at the same workspace, re-send the compiled node
  prompt, and pick up the next open ledger item.
- **Clean-context review** — an independent supervisor can catch drift the executor cannot see.
- **Forced convergence** — growth is periodically stopped, measured, and simplified.
- **Low-friction owner decisions** — genuine owner-only calls arrive as a short
  recommended A/B/C choice, not a technical homework assignment.

The skill is Markdown policy (compile / interview), not an orchestration
framework. **On this fork the default engine path is the runner CLI:** after
compile, the host AI must explicitly run `longgraph run …`. Skill-only `/loop`
paste does **not** harden gates. Calling the runner “optional” is wrong for
this fork’s default. Grok Build still has **no wake edge** — default is
`longgraph run --host prompt-only <run_dir>` (or paste of the emitted `/loop`
lines when the host cannot shell). Grok does not auto-invoke without a shell
step.

## Multi-task loops & switching hosts

**One loop is a queue, not a single story.** Each round still completes one
independently verifiable ledger work item end-to-end (implement → verify → record). That
item may be one coherent workset of coupled changes sharing a behavior claim, write set,
and gate; unrelated work stays separate. The ledger can hold many long items at once —
related milestones *or* unrelated backlog (the gate-wait backlog pattern is the extreme
case: useful work with no dependency on the item under audit). You do not need a new graph
every time the next long task is about something else.

**The host is swappable; the files are not.** A compiled loop-graph run freezes
prompts and state under `.longgraph/<date-slug>/`. To continue elsewhere:

1. Use a workspace that can see those files (and the project).
2. Re-send the same frozen executor (and, if used, supervisor) prompt on the new host.
3. The node reads `ledger.md` / `directives.md` and continues from the next open item.

You are not exporting chat transcripts. Invocation syntax still follows each host’s
dialect ([per-host references](skills/loop-graph/references/)) — only the *progress* is portable.

## Is longgraph the right tool?

| Your task shape | Choose | What you get |
| --- | --- | --- |
| One self-contained goal that fits a normal task/session | Use the host's ordinary task or goal directly | No longgraph wrapper or extra prompt layer |
| A feature, integration, migration, or behavior requirement across many verified slices | [**`/loop-deliver`**](skills/loop-deliver/README.md) | A requirement pack on the shared graph, with traceable acceptance proof |
| Multi-round unused / duplicate / reuse / slim (same two-node graph) | [**`/loop-converge`**](skills/loop-converge/README.md) | The shared compiler with a pre-bound convergence pack |
| Compare feasible approaches with open-source evidence, primary research, and experiments | [**`/loop-research`**](skills/loop-research/README.md) | An evidence-led decision pack; it selects only when results are comparable |
| Many rounds with a custom shape not covered above | [**longgraph / loop-graph**](skills/loop-graph/README.md) | The shared compiler for a custom graph run |

**Rule of thumb:** if you do not need the graph, do not use longgraph.

## Quick start

**Default on this fork:** install/link the skill (compile / policy) → install
the runner → the host AI **explicitly runs** `longgraph run …`. Skill-only
`/loop` paste is not the primary default. The skill does not auto-start the
engine and does not harden gates by itself.

### 1. Clone this fork and link the skill

Prefer this checkout — do not curl upstream `levi-qiao` unless you intend that tree:

```sh
git clone https://github.com/Samek86/longgraph-skill.git
cd longgraph-skill
./install.sh
```

`./install.sh` symlinks `/longgraph`, `/loop-converge`, `/loop-deliver`, and
`/loop-research` into hosts whose loaders follow symlinks (Codex, Cursor, Grok
Build). Claude Code does not load those symlinks; install the plugin there for
compile/policy, then still install the runner:

```text
/plugin marketplace add Samek86/longgraph-skill
/plugin install longgraph@longgraph-skill
```

### 2. Install the runner (default engine)

```sh
cd runner
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

PowerShell (Windows native):

```powershell
cd runner
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### 3. Design a run (compile only)

Invoke `/longgraph`; it routes cleanup to `/loop-converge`, requirements to
`/loop-deliver`, and evidence-led option selection to `/loop-research`. It detects the
current host, inspects the workspace, and asks only for unresolved owner decisions before
compiling the run. Use `loop-graph` directly only for a genuinely custom run shape.

Authoring and runtime stay separate: the author skill compiles the work but never
executes it. Generated nodes follow their frozen run contract under
`.longgraph/<date-slug>/`.

### 4. Default: run the engine

After compile (or using a fixture copy), the **agent MUST explicitly execute**
`longgraph run …`. Never assume the skill auto-starts the engine. If the host
can run a shell, **prefer the CLI over manual `/loop` paste**.

```sh
cp -R tests/fixtures/add-tests-to-cli /tmp/add-tests-to-cli
longgraph run --host mock /tmp/add-tests-to-cli          # local apply/verify loops; copy first
longgraph run --host prompt-only /tmp/add-tests-to-cli   # emit DualTimer /loop blocks; does not close
```

PowerShell (Windows native) — the agent **MUST** still execute `longgraph run …`:

```powershell
Copy-Item -Recurse tests\fixtures\add-tests-to-cli $env:TEMP\add-tests-to-cli
longgraph run --host mock $env:TEMP\add-tests-to-cli
longgraph run --host prompt-only $env:TEMP\add-tests-to-cli
```

**Grok Build:** still no wake edge. Default =
`longgraph run --host prompt-only <run_dir>` (or document paste of the emitted
`/loop` lines). Do not claim Grok auto-invokes without a shell step. See
[Grok Build](skills/loop-graph/references/grok.md).

Prompt-only paste of emitted `/loop` lines is the fallback when the CLI is
unavailable — see [host compatibility](#host-compatibility).

Record a stranger walk-through with the [docs dry-run](docs/ship/DOCS-DRY-RUN.md).
Supported Host / Python / OS: [Support surface](docs/ship/SUPPORT.md)
(Python 3.11–3.12 on `ubuntu-latest` and `windows-latest`; macOS is not
claimed). DualTimer live soak is not claimed.

## How the graph works

| Role | Responsibility | Durable edge |
| --- | --- | --- |
| **Executor** | Works one independently verifiable ledger work item, verifies it in the same round, then records the result | Reads and writes `ledger.md` |
| **Supervisor** | Re-verifies from its own separate context, checkpoints passing work, and corrects drift | Reads the ledger; steers only through the directives edge (live queue + cold archive) |
| **Scout** *(optional)* | Researches a bounded question away from the critical path | Writes a findings file read only on reference |

The load-bearing rule is **one node = one prompt + one single-writer edge**.
The ledger has exactly one writer. The supervisor never shares the executor’s
context, never edits its scoreboard, and steers only through the one-way
directives edge.

For the rationale behind every constraint, read
[the methodology](lib/methodology.md). For the node and edge model, see
[the loop-graph model](skills/loop-graph/docs/model.md).

## Host compatibility

| Host | loop-graph execution |
| --- | --- |
| [**Codex**](skills/loop-graph/references/codex.md) | ✅ detects the host and directly creates both runtime nodes |
| [**Claude Code**](skills/loop-graph/references/claude-code.md) | ✅ detects the host and directly creates two background runtime sessions when capability checks pass |
| [**Grok Build**](skills/loop-graph/references/grok.md) | Default: AI runs `longgraph run --host prompt-only <run_dir>` (no wake edge; no auto-invoke). Manual `/loop` paste is fallback |
| [**Cursor**](skills/loop-graph/references/cursor.md) | Default: AI runs `longgraph run --host …`. `/loop` paste is fallback when CLI unavailable |
| [**shell / cron**](skills/loop-graph/references/shell-cron.md) | Default: `longgraph run --host …` |

Authoritative syntax, pacing, context carry, and hooks live in separate
[per-host references](skills/loop-graph/references/), so authoring loads only the selected host. Mid-run host switches reuse the same
durable run directory; only how you start each tick changes.

## Repository map

| Path | Purpose |
| --- | --- |
| [Root `SKILL.md`](SKILL.md) | `/longgraph` router; chooses the focused pack or custom compiler path |
| [Loop-graph compiler](skills/loop-graph/SKILL.md) | Generates the shared executor, supervisor, ledger, directive, and ops artifacts |
| [loop-converge](skills/loop-converge/SKILL.md) | Preset entry: code-convergence interview → same loop-graph compile |
| [loop-deliver](skills/loop-deliver/SKILL.md) | Preset entry: requirement-delivery interview → same compile |
| [loop-research](skills/loop-research/SKILL.md) | Preset entry: evidence-led solution-selection interview → same compile |
| [Preset contract](skills/loop-graph/docs/preset-contract.md) | Boundary between the shared compiler and goal-specific packs |
| [`lib/`](lib) | Shared methodology |
| [Host references](skills/loop-graph/references) | One independently loaded owner for each host's runtime facts |
| [Worked examples](skills/loop-graph/examples) | Public-Git self-iteration plus fictional ledgers showing gates in action |
| [Public / private boundary](docs/public-private-boundary.md) | What may enter the public tree vs stay project-local |
| [Runner CLI](runner/README.md) | **Default engine** for compiled run dirs — AI must run `longgraph run --host …`. `--host prompt-only` (safe emit), `grok-bot` DualTimer, `mock` tests only. Version `0.4.0-rc.1` on `main` |
| [Public claims](docs/ship/PUBLIC_CLAIMS.md) | P1–P10 bound to named pytest (not marketing copy) |
| [D2 Go/No-Go](docs/ship/D2-GO-NOGO.md) | R pack: coding evidence READY; live `0.4.0-rc.1` on `main`; stable publish ack + DualTimer soak stay owner |
| [CHANGELOG](CHANGELOG.md) | Phase 0–1c + H0–H2 + D2 candidate; new tags are owner-only |
| [Known issues](KNOWN_ISSUES.md) | `0.4.0-rc.1` / mock N=50 on `main`; DualTimer soak + stable publish ack stay owner |
| [Docs dry-run](docs/ship/DOCS-DRY-RUN.md) | S4: stranger follows README for mock + prompt-only on a fixture copy |
| [Support surface](docs/ship/SUPPORT.md) | S5: CLI hosts + Python 3.11/3.12 + ubuntu-latest / windows-latest; CI matrix bound |
| [SECURITY.md](SECURITY.md) | Workspace escape denied, no secrets in fixtures, runner does not `git push` |

## Governance

longgraph applies its own anti-bloat rule to the library: **no prompt enters
without a real run that proved its value.** Curated and opinionated beats
comprehensive.

Contributions are welcome. Start with [the contribution guide](CONTRIBUTING.md).

## 🔒 Security and Privacy

This fork includes additional security tooling:

```bash
# Scan .longgraph directory before committing
./scripts/scrub-longgraph-secrets.sh

# Scan a specific run
./scripts/scrub-longgraph-secrets.sh .longgraph/2026-09-08-auth-migration

# Dry run to see what would be scanned
./scripts/scrub-longgraph-secrets.sh --dry-run
```

See [FORK.md](FORK.md) for details.

## 📊 Observability

To track run status:

```bash
# Check status of all runs
find .longgraph -name status.json -exec jq . {} \;
```

See [docs/observability/status-schema.md](docs/observability/status-schema.md) for schema and integration details.

## Credits

The loop-graph skill grew from real runs and community input. A
[public-Git self-iteration case](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md)
records how the method was hardened into this library. Special thanks to
[@BrightProgrammer7](https://github.com/BrightProgrammer7) for the
`migrate-blob-storage` example and the discussions that sharpened milestone
gates and the node/edge vocabulary.

Fork enhancements are maintained by [Samek86](https://github.com/Samek86).

## License

[MIT](LICENSE) © 2026 [levi-qiao](https://github.com/levi-qiao)

Fork enhancements © 2026 [Samek86](https://github.com/Samek86)
