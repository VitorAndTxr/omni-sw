# Changelog

All notable changes to omni-sw are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.6.0] — 2026-03-21

### Added

- **Timestamped document storage:** Phase artifacts now written to `agent_docs/<short-desc>-<YYYY_MM_DD_HH_MM>/` per SDLC run, isolating working documents across runs. `docs/` reserved for maintained descriptive documentation (architecture overview, flow diagrams).
- `DOCS_PATH` resolved path injected into all agent prompts via the environment block, alongside existing `PROJECT_ROOT`, `SCRIPT_PATH`, etc.
- `state init` accepts `--project-root` and `--short-description` to create the timestamped subfolder. Short description auto-derived from objective when omitted.
- `resolve_artifact_path()` in `phase.py` dynamically maps `docs/` artifact templates to the current run's `DOCS_PATH`.
- `get_docs_path()` helper in `state.py` with backward-compatible fallback to `docs/` when STATE.json has no `docs_path` field.

### Fixed

- **`backlog_cmd.py` `query_by_profile()`:** Was passing `backlog_path` twice (once in cmd list, once appended by `run_backlog_cmd`), causing every `agency_cli backlog query` call to crash.
- **`backlog_cmd.py` `run_backlog_cmd()`:** Argument order fixed — `backlog_path` now inserted right after subcommand name per `backlog_manager.py` parser expectations.
- **`init_cmd.py` `find_backlog_script()`:** Glob results now sorted by path length to prefer the closest match to scan root.
- **`init_cmd.py` `handle_init()`:** All output paths normalized to forward slashes for bash on Windows.
- **`init_cmd.py` `install_hooks()`:** Hook command now uses `sys.executable` (resolved at install time) instead of bare `python`, fixing hook failures when Python is not on PATH in the hook runner context.
- **`pre_implement_guard.py`:** Now reads `docs_path` from STATE.json instead of hardcoding `docs/VALIDATION.md`.

### Changed

- STATE.json version bumped to `1.1` with new `docs_path` field.
- All agent skills (PM, PO, TL, Dev, QA) reference `{DOCS_PATH}/` instead of `docs/` for phase artifacts.
- Orchestrator gate parse commands, report commands, and decision log path use `{DOCS_PATH}`.
- PM/TL Document phase updated to maintain `docs/` with descriptive documentation (architecture overview, diagrams) for human consumption.
- Checkpoint artifact inventory resolves through dynamic `docs_path`.

---

## [0.5.1] — 2026-02-27

### Added

- Apache License 2.0 (`LICENSE` at project root).
- Reinforced Mermaid diagram standard across all agent skills (tl, orchestrator, dev, pm, qa, api-doc-scraper, apply-progressive-disclosure) with consistent MUST-level constraint language.

---

## [0.5.0] — 2026-02-27

### Changed

- Refactored agency documentation for clarity and consistency across all agent reference files and phase walkthroughs.
- Simplified scripts and CLI usage patterns; removed redundant commands and consolidated overlapping operations.

---

## [0.4.0] — 2026-02-24

### Added

- **Metrics reporting** for the SDLC workflow: the orchestrator now generates a metrics summary at the end of each run, covering phase durations, gate iterations, and story throughput.
- **Enhanced state machine** with richer phase status tracking, agent-level status fields, and crash recovery support via `CHECKPOINT.md`.
- **Decision logging** (`docs/DECISIONS.md`): agents record significant architectural and product decisions during each phase, creating an append-only audit trail.

---

## [0.3.0] — 2026-02-22

### Added

- **Report generation commands** in `agency_cli.py`: `report phase-summary`, `report metrics`, and `report gate` produce structured summaries consumable by the orchestrator without re-invoking LLMs.
- **Token analysis commands**: `scan` and `token-analysis` inspect skill and CLAUDE.md files for context cost, supporting the progressive disclosure optimization workflow.
- **Phase execution documentation** (`skills/orchestrator/references/phase-details.md`, `phase-matrix.md`): authoritative reference tables for agent/model assignments, gate conditions, and phase dependencies.
- **Backlog migration documentation**: step-by-step guide for migrating legacy `docs/BACKLOG.md` markdown files to the JSON backlog format.

### Removed

- Obsolete `xlsx` skill files replaced by the dedicated `xlsx` utility skill.

---

## [0.2.0] — 2026-02-17

### Added

- **Orchestrator skill** (`/orchestrator`): end-to-end SDLC conductor that spawns PM, PO, TL, Dev, and QA agents in the correct sequence, evaluates gates deterministically via `agency_cli.py`, and handles feedback loops automatically.
- **Phase-agent mapping**: `agency_cli.py phase prepare` command combines state update, agent ordering, and prompt generation into a single CLI call, reducing orchestrator context growth.
- **Parallel pipeline execution**: orchestrator detects independent feature groups and runs Implement → Review → Test in parallel per feature, converging at the Document phase.
- **Backlog integration enforcement**: all agents now read and write the backlog exclusively through `backlog_manager.py` via `agency_cli.py`, enforcing the role-based permission matrix (PM/PO create, TL edits, all agents transition status).
- **Usage guidelines** consolidated in `docs/agency/` for agent reference, phase walkthrough, architecture diagrams, hooks system, and extension guide.

---

## [0.1.0] — 2026-02-06

### Added

- Initial agency structure: five role-based agents (PM, PO, TL, Dev, QA) as Claude Code skills, each with phase-specific modes (`plan`, `design`, `validate`, `implement`, `review`, `test`, `document`).
- Seven-phase SDLC workflow with dual validation gate (PM + TL) and feedback loops back to Plan, Design, and Implement.
- **Backlog system** (`/backlog` skill): JSON-backed user story management with CRUD operations, status transitions, and role-based access control.
- `agency_cli.py` — Python CLI for deterministic operations: project root resolution, backlog management, gate parsing, state tracking, and batch phase transitions.
- Artifact templates for all phase outputs: `PROJECT_BRIEF.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `VALIDATION.md`, `REVIEW.md`, `TEST_REPORT.md`, `API_REFERENCE.md`.
- `CLAUDE_TEMPLATE.md` for onboarding new projects (stack, conventions, domain glossary, forbidden patterns, agent overrides).
- **Shared agent-common setup** (`skills/shared/agent-common.md`): unified project root resolution, backlog integration rules, state tracking protocol, and decision log format shared across all agents.
- Hooks system (`.claude/hooks.json`): project-level automated guardrails triggered on tool events (`PreToolUse`, `PostToolUse`).
- `README_AGENCY.md`: top-level hub with role-phase matrix and documentation index.
- `docs/USAGE_GUIDE.md`: full command reference covering both the minimum viable workflow and the full multi-participant workflow.
