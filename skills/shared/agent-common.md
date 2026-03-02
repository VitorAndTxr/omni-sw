# Agent Common Setup

Shared setup for all agency agents (PM, PO, TL, Dev, QA). Each agent's SKILL.md references this file.

## Agency CLI

The `agency_cli.py` script handles all deterministic operations (path resolution, model lookup, phase routing, gate parsing, batch transitions, token analysis).

If the orchestrator provided `CLI_PATH` in your spawn prompt, use it directly as `{CLI}`. Otherwise, find this skill's own SKILL.md and derive the CLI path:

```
Glob pattern: "**/<your-skill-name>/SKILL.md"
```

The CLI is always at `../shared/scripts/agency_cli.py` relative to your skill's directory. Verify it exists, then store as `{CLI}`.

## Project Root Resolution

If the orchestrator provided `PROJECT_ROOT`, `SCRIPT_PATH`, and `BACKLOG_PATH` in your spawn prompt, use those directly. Otherwise, resolve once via CLI:

```bash
python {CLI} init --scan-root {workspace}
# Returns JSON: project_root, script_path, backlog_path, team_name, claude_md
```

All artifact paths (`docs/`, `src/`, `tests/`) are relative to the project root.

## Backlog Integration

**NEVER read `backlog.json` or `BACKLOG.md` directly** — always use `backlog_manager.py` via Bash.

Pass `--caller <agent>` on every command. The script rejects unauthorized operations.

For batch transitions (e.g., transitioning all stories for a phase):
```bash
python {CLI} backlog phase-transition --phase {phase} --caller {role} --backlog-path {BACKLOG_PATH} --script-path {SCRIPT_PATH}
```

To validate a transition before executing:
```bash
python {CLI} backlog validate-transition --from "Ready" --to "In Design"
```

### Permission Matrix

| Operation  | po | pm | tl | dev | qa |
|------------|----|----|----|----|-----|
| Create US  | Y  | Y  | N  | N  | N  |
| Edit US    | Y  | Y  | Y  | N  | N  |
| Status     | Y  | Y  | Y  | Y  | Y  |
| Delete US  | Y  | Y  | N  | N  | N  |
| Question   | Y  | Y  | Y  | Y  | Y  |

## Phase Routing

Route to the phase matching the argument after `/{role}` (ask if none provided).

## Backlog Render Rule

When performing multiple mutations in sequence (creating stories, changing statuses), call `render` only once after all mutations are complete. Do NOT render after every individual mutation.

## State Tracking

All agents must update the project state when starting and completing phase work. This enables workflow enforcement, crash recovery, and metrics collection.

### On Phase Start

Before doing any phase work, update state:

```bash
python {CLI} state update --state-path {STATE_PATH} --phase {current_phase} --status in_progress --agent {agent_name} --agent-status in_progress
```

Where `{STATE_PATH}` is `{project_root}/agent_docs/agency/STATE.json`. If the orchestrator provided `STATE_PATH` in your spawn prompt, use it directly. Otherwise derive it from project root.

If STATE.json doesn't exist yet, the first agent (typically pm-plan via orchestrator) should initialize it:

```bash
python {CLI} state init --project {project_name} --objective "{objective}" --state-path {STATE_PATH}
```

### On Phase Completion

After producing all artifacts for your phase:

```bash
python {CLI} state update --state-path {STATE_PATH} --phase {current_phase} --status completed --agent {agent_name} --agent-status completed
```

### On Gate Verdict (Gate phases only: validate, review, test)

After writing your verdict, record it in state:

```bash
# Validate (PM or TL):
python {CLI} state gate-record --state-path {STATE_PATH} --phase validate --verdict "APPROVED" --pm APPROVED --tl APPROVED

# Review (TL):
python {CLI} state gate-record --state-path {STATE_PATH} --phase review --verdict PASS

# Test (QA):
python {CLI} state gate-record --state-path {STATE_PATH} --phase test --verdict PASS --tests-passed 42 --tests-failed 0
```

### Important Rules

- State updates are **non-blocking** — if the state command fails, continue your work and report the failure.
- The orchestrator is responsible for `state init`. Individual agents only call `state update` and `state gate-record`.
- Assist agents do NOT update phase status (only their agent status).

## Decision Log

When making significant design decisions, trade-offs, or choosing between alternatives, record them:

```bash
python {CLI} decision add --decisions-path {project_root}/docs/DECISIONS.md --phase {phase} --agent {role} --title "Short decision title" --context "Why this decision was needed" --alternatives "Option A (rejected: reason), Option B (rejected: reason)" --decision "What was decided" --impact "Affected stories or components"
```

### When to Record Decisions

- **TL in Design:** Architecture choices, technology selections, pattern decisions
- **TL in Review:** Accepted deviations from architecture, new patterns adopted
- **Dev in Implement:** Implementation trade-offs, library choices within scope
- **PM in Validate:** Scope changes, requirement reinterpretations
- **QA in Test:** Test strategy decisions, coverage trade-offs

### Important Rules

- Only record decisions that affect the project direction — not routine implementation choices.
- The decision log is append-only. Never edit or delete existing entries.
- If unsure whether something qualifies as a "decision", err on the side of recording it.
