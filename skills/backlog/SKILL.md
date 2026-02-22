---
name: backlog
description: >-
  Backlog management system — Manages user stories as structured JSON with role-based
  access control, replacing markdown-based BACKLOG.md. Provides CRUD operations for
  user stories, status tracking, acceptance criteria, dependency maps, and auto-generated
  markdown summaries. Enforces agency permissions: only po/pm create stories, only
  po/pm/tl edit descriptions, all agents can change status. Supports migration from
  legacy markdown BACKLOG.md via review teams. Use when: (1) any agent needs to create,
  read, update, or delete user stories, (2) agent mentions "backlog", "user story",
  "US-", "acceptance criteria", "story status", (3) po/pm is producing backlog in Plan
  phase, (4) any agent needs to query stories by status/feature/priority, (5) generating
  BACKLOG.md summary from JSON data, (6) migrating an old docs/BACKLOG.md to the new
  JSON format.
user-invocable: false
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Backlog Management System

Structured JSON-based backlog replacing the markdown template. All backlog data lives in `agent_docs/backlog/` relative to the project root.

## File Layout

```
{project_root}/agent_docs/backlog/
├── backlog.json    ← source of truth (structured data)
└── BACKLOG.md      ← auto-generated readable summary
```

## Script Resolution

The script `backlog_manager.py` is bundled with this skill but its absolute path varies depending on installation method (plugin cache, `--plugin-dir`, or `~/.claude/skills/`). Resolve it **once per session** using Glob, then reuse the result:

```bash
# Run once at session start via Glob tool:
Glob pattern: "**/backlog/scripts/backlog_manager.py"
```

Store the result as `{SCRIPT}` for all subsequent commands. This costs one Glob call and avoids hardcoded paths.

## Permission Matrix

| Operation  | po | pm | tl | dev | qa |
|------------|----|----|----|----|-----|
| Create US  | Y  | Y  | N  | N  | N  |
| Edit US    | Y  | Y  | Y  | N  | N  |
| Status     | Y  | Y  | Y  | Y  | Y  |
| Delete US  | Y  | Y  | N  | N  | N  |
| Question   | Y  | Y  | Y  | Y  | Y  |

Pass `--caller <agent>` on every command. The script rejects unauthorized operations.

## Commands Reference

All commands output JSON to stdout. The `BACKLOG_PATH` is `{project_root}/agent_docs/backlog/backlog.json`.

### Initialize backlog

```bash
python {script} init {BACKLOG_PATH}
```

### Get next available story ID

```bash
python {script} next-id {BACKLOG_PATH}
```

### Create user story

```bash
python {script} create {BACKLOG_PATH} \
  --id US-001 --title "Story title" \
  --role "user role" --want "capability" --benefit "business value" \
  --feature "Feature Area" --priority Must \
  --caller po \
  --ac '[{"id":"AC-001.1","given":"context","when":"action","then":"result"}]' \
  --depends "US-002,US-003"
```

Priority values: `Must`, `Should`, `Could`, `Won't` (MoSCoW).

### Edit user story

```bash
python {script} edit {BACKLOG_PATH} --id US-001 --caller tl \
  --title "New title" --priority Should --notes "Updated notes"
```

Accepts any combination of: `--title`, `--role`, `--want`, `--benefit`, `--priority`, `--notes`, `--feature`, `--ac`, `--depends`.

### Change status

```bash
python {script} status {BACKLOG_PATH} --id US-001 --status "In Progress" --caller dev
```

Valid statuses: `Draft`, `Ready`, `In Design`, `Validated`, `In Progress`, `In Review`, `In Testing`, `Done`, `Blocked`, `Cancelled`.

### List / filter stories

```bash
python {script} list {BACKLOG_PATH} --status Ready --format summary
python {script} list {BACKLOG_PATH} --feature "Authentication" --format json
python {script} list {BACKLOG_PATH} --priority Must --format table
python {script} list {BACKLOG_PATH} --fields id,title,status
python {script} list {BACKLOG_PATH} --status "In Progress" --limit 5
python {script} list {BACKLOG_PATH} --limit 10 --offset 10
```

- `--fields <field1,field2,...>` — return only the specified fields. Overrides format defaults for both `json` and `summary`. Valid fields: `id`, `title`, `feature_area`, `priority`, `role`, `want`, `benefit`, `acceptance_criteria`, `notes`, `dependencies`, `status`.
- `--limit <N>` — return at most N stories after filtering.
- `--offset <N>` — skip the first N stories before applying limit.
- The `json` format returns story content fields only (no audit metadata like `history`, `created_at`, `updated_at`, `created_by`). Use `get` for full audit data on a single story.

### Aggregate stats (counts only)

```bash
python {script} stats {BACKLOG_PATH}
```

Returns counts by status, priority, and feature area without any story content. Use this instead of `list` when you only need progress numbers (e.g., gate checks, phase overviews).

Example output:
```json
{"total": 32, "by_status": {"Ready": 5, "In Progress": 3}, "by_priority": {"Must": 12}, "by_feature": {"Auth": 8}}
```

### Get single story (full detail)

```bash
python {script} get {BACKLOG_PATH} --id US-001
```

Returns the complete story object including all audit fields (`history`, `created_at`, `updated_at`, `created_by`). Use for single-story audits and detailed inspection.

### Delete story

```bash
python {script} delete {BACKLOG_PATH} --id US-001 --caller po
```

### Render BACKLOG.md

```bash
python {script} render {BACKLOG_PATH} --output {project_root}/agent_docs/backlog/BACKLOG.md
```

When performing multiple mutations in sequence (e.g., creating multiple stories, transitioning multiple statuses), call `render` only once after all mutations are complete. Do NOT render after every individual mutation.

### Manage open questions

```bash
# Ask a question
python {script} question {BACKLOG_PATH} --text "Is OAuth2 in scope?" --caller po

# Resolve a question
python {script} question {BACKLOG_PATH} --id Q-001 --resolve --answer "Yes, v2" --caller pm
```

## Integration with Agent Skills

When an agent skill (po, pm, tl, dev, qa) needs to interact with the backlog, resolve paths and call the script via Bash:

1. Resolve `{project_root}` by locating `CLAUDE.md` at the `[businessUnit]/[project]/` level.
2. Set `BACKLOG_PATH={project_root}/agent_docs/backlog/backlog.json`.
3. Resolve `{SCRIPT}` via Glob: `**/backlog/scripts/backlog_manager.py` (once per session, reuse the result).
4. Call the appropriate command with `--caller` matching the agent's role.
5. After completing a batch of mutations, call `render` once to update `BACKLOG.md`. Do NOT render after every individual mutation.

## Mutation Response Format

`create` and `edit` return slim confirmations to minimize context usage:
- **create:** `{"success": true, "id": "US-001"}`
- **edit:** `{"success": true, "id": "US-001", "changes": ["title", "priority"]}`

Use `get --id <US-XXX>` to retrieve the full story if needed after mutation.

## Query Selection Guide

| Need | Command |
|------|---------|
| Progress overview (counts only) | `stats` |
| Story list (IDs + titles + status) | `list --format summary` |
| Story list (specific fields) | `list --fields id,title,acceptance_criteria` |
| Story list (full detail minus audit) | `list --format json` |
| Single story (all fields + history) | `get --id US-XXX` |

## Status Transitions by Phase

| Phase     | Agent | Typical Transitions                          |
|-----------|-------|---------------------------------------------|
| Plan      | PO    | → Draft → Ready                             |
| Design    | TL    | Ready → In Design                           |
| Validate  | PM/TL | In Design → Validated                       |
| Implement | Dev   | Validated → In Progress → In Review         |
| Review    | TL    | In Review (stays, or → In Progress if issues)|
| Test      | QA    | In Review → In Testing → Done               |

## Migration from Legacy BACKLOG.md

For migration workflows, read [references/migration.md](references/migration.md). Only triggered by `/po migrate` or `/pm migrate`.

## Team Orchestration

For team-based workflows using TeamCreate/Task tools, see [references/team-orchestration.md](references/team-orchestration.md).

## JSON Schema

For the complete data structure, see [references/schema.md](references/schema.md).
