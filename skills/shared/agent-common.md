# Agent Common Setup

Shared setup for all agency agents (PM, PO, TL, Dev, QA). Each agent's SKILL.md references this file.

## Agency CLI

The `agency_cli.py` script handles all deterministic operations (path resolution, model lookup, phase routing, gate parsing, batch transitions, token analysis). Resolve its path once per session:

```bash
CLI=$(python -c "import glob; print(glob.glob('**/shared/scripts/agency_cli.py', recursive=True)[0])")
```

If the orchestrator provided `CLI_PATH` in your spawn prompt, use it directly.

## Project Root Resolution

If the orchestrator provided `PROJECT_ROOT`, `SCRIPT_PATH`, and `BACKLOG_PATH` in your spawn prompt, use those directly. Otherwise, resolve once via CLI:

```bash
python $CLI init --scan-root <workspace>
# Returns JSON: project_root, script_path, backlog_path, team_name, claude_md
```

All artifact paths (`docs/`, `src/`, `tests/`) are relative to the project root.

## Backlog Integration

**NEVER read `backlog.json` or `BACKLOG.md` directly** — always use `backlog_manager.py` via Bash.

Pass `--caller <agent>` on every command. The script rejects unauthorized operations.

For batch transitions (e.g., transitioning all stories for a phase):
```bash
python $CLI backlog phase-transition --phase <phase> --caller <role> --backlog-path $BACKLOG_PATH --script-path $SCRIPT_PATH
```

To validate a transition before executing:
```bash
python $CLI backlog validate-transition --from "Ready" --to "In Design"
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
