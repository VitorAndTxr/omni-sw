# Backlog Commands Reference

All commands output JSON to stdout. The `BACKLOG_PATH` is `{project_root}/agent_docs/backlog/backlog.json`.

## Initialize backlog

```bash
python {script} init {BACKLOG_PATH}
```

## Get next available story ID

```bash
python {script} next-id {BACKLOG_PATH}
```

## Create user story

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

## Edit user story

```bash
python {script} edit {BACKLOG_PATH} --id US-001 --caller tl \
  --title "New title" --priority Should --notes "Updated notes"
```

Accepts any combination of: `--title`, `--role`, `--want`, `--benefit`, `--priority`, `--notes`, `--feature`, `--ac`, `--depends`.

## Change status

```bash
python {script} status {BACKLOG_PATH} --id US-001 --status "In Progress" --caller dev
```

Valid statuses: `Draft`, `Ready`, `In Design`, `Validated`, `In Progress`, `In Review`, `In Testing`, `Done`, `Blocked`, `Cancelled`.

## List / filter stories

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

## Aggregate stats (counts only)

```bash
python {script} stats {BACKLOG_PATH}
```

Returns counts by status, priority, and feature area without any story content. Use this instead of `list` when you only need progress numbers (e.g., gate checks, phase overviews).

Example output:
```json
{"total": 32, "by_status": {"Ready": 5, "In Progress": 3}, "by_priority": {"Must": 12}, "by_feature": {"Auth": 8}}
```

## Get single story (full detail)

```bash
python {script} get {BACKLOG_PATH} --id US-001
```

Returns the complete story object including all audit fields (`history`, `created_at`, `updated_at`, `created_by`). Use for single-story audits and detailed inspection.

## Delete story

```bash
python {script} delete {BACKLOG_PATH} --id US-001 --caller po
```

## Render BACKLOG.md

```bash
python {script} render {BACKLOG_PATH} --output {project_root}/agent_docs/backlog/BACKLOG.md
```

When performing multiple mutations in sequence (e.g., creating multiple stories, transitioning multiple statuses), call `render` only once after all mutations are complete. Do NOT render after every individual mutation.

## Manage open questions

```bash
# Ask a question
python {script} question {BACKLOG_PATH} --text "Is OAuth2 in scope?" --caller po

# Resolve a question
python {script} question {BACKLOG_PATH} --id Q-001 --resolve --answer "Yes, v2" --caller pm
```
