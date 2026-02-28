# backlog

JSON-backed user story management system used internally by the agency agents during the SDLC workflow. Replaces the flat `docs/BACKLOG.md` markdown file with a structured data store that enforces role-based permissions, tracks status transitions, and auto-generates a markdown summary.

> **Note:** This skill is used by agents (PM, PO, TL, Dev, QA) as part of their phase workflows. It is not intended for direct user invocation. To interact with the backlog as a user, work through the appropriate agent skill (`/omni-sw:po plan`, `/omni-sw:pm migrate`, etc.).

## File layout

```
{project-root}/agent_docs/backlog/
├── backlog.json      ← source of truth (never edit manually)
└── BACKLOG.md        ← auto-generated summary (read-only view)
```

## Permissions

Each operation is gated by the caller role. Agents pass `--caller <role>` on every command.

| Operation | pm | po | tl | dev | qa |
|-----------|----|----|----|----|-----|
| Create story | Y | Y | N | N | N |
| Edit description | Y | Y | Y | N | N |
| Change status | Y | Y | Y | Y | Y |
| Delete story | Y | Y | N | N | N |
| Query / read | Y | Y | Y | Y | Y |

## Status lifecycle

Stories move through statuses as the workflow progresses:

```
Draft → Ready → In Design → Validated → In Progress → In Review → In Testing → Done
```

| Phase | Agent | Transition |
|-------|-------|-----------|
| Plan | PO | → Draft → Ready |
| Design | TL | Ready → In Design |
| Validate | PM / TL | In Design → Validated |
| Implement | Dev | Validated → In Progress → In Review |
| Review | TL | In Review (or → In Progress if issues) |
| Test | QA | In Review → In Testing → Done |

## Commands (agent reference)

Agents interact with the backlog exclusively through `backlog_manager.py` via `agency_cli.py`. Direct JSON edits are not allowed.

### Querying

| Goal | Command |
|------|---------|
| Progress overview (counts only) | `list --format summary` |
| Story list with titles and status | `list --fields id,title,status` |
| Stories in a specific status | `list --status "In Progress"` |
| Single story with full detail | `get --id US-001` |
| Aggregate stats | `stats` |

### Mutations

```bash
# Create a story (po or pm only)
python {CLI} backlog create --caller po --title "..." --feature-area "..." --priority high ...

# Edit story fields (po, pm, tl only)
python {CLI} backlog edit --caller tl --id US-001 --title "Updated title"

# Transition status (any agent)
python {CLI} backlog status --caller dev --id US-001 --status "In Progress"

# Re-render BACKLOG.md from current JSON
python {CLI} backlog render --backlog-path {BACKLOG_PATH} --script-path {SCRIPT_PATH}
```

**Render rule:** When making multiple mutations in sequence (e.g., creating many stories during Plan), call `render` **once** after all mutations are complete — not after each individual change.

## Story schema

Key fields stored per user story:

| Field | Description |
|-------|-------------|
| `id` | Auto-assigned (US-001, US-002, …) |
| `title` | Short imperative description |
| `feature_area` | Feature grouping for filtering and pipeline parallelism |
| `priority` | `critical`, `high`, `medium`, `low` |
| `status` | Current workflow status |
| `acceptance_criteria` | Given/When/Then conditions |
| `dependencies` | List of story IDs this story depends on |
| `story_points` | Optional effort estimate |

For the complete schema, see `skills/backlog/references/schema.md`.

## Migration from legacy BACKLOG.md

If a project has an existing `docs/BACKLOG.md` in the old markdown format, use the migration workflow:

```
/omni-sw:pm migrate
```

or

```
/omni-sw:po migrate
```

The migration skill spawns a review team to parse the old markdown, create JSON stories, and validate the conversion. See `skills/backlog/references/migration.md` for details.
