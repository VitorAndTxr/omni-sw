# Agent Common Setup

Shared setup for all agency agents (PM, PO, TL, Dev, QA). Each agent's SKILL.md references this file.

## Project Root Resolution

All artifact paths (`docs/`, `src/`, `tests/`) are relative to the **project root** — identified by locating `CLAUDE.md` at the `[businessUnit]/[project]/` level. Template paths like `docs/templates/X.md` resolve to `~/.claude/docs/templates/X.md`.

## Backlog Integration

**NEVER read `backlog.json` or `BACKLOG.md` directly** — always use `backlog_manager.py` via Bash.

**Path resolution:** If the orchestrator provided `SCRIPT_PATH` and `BACKLOG_PATH` in your spawn prompt, use those directly. Otherwise, resolve once per session:
- `BACKLOG_PATH={project_root}/agent_docs/backlog/backlog.json`
- `SCRIPT` via Glob: `**/backlog/scripts/backlog_manager.py`

Pass `--caller <agent>` on every command. The script rejects unauthorized operations.

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
