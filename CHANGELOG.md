# Changelog

All notable changes to omni-sw are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
