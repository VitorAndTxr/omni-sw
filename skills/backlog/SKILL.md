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

## Permissions

Pass `--caller <agent>` on every command. The script rejects unauthorized operations. See `shared/agent-common.md` for the full permission matrix.

## Commands

For the full commands reference (init, create, edit, status, list, stats, get, delete, render, question), see [references/commands.md](references/commands.md).

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
