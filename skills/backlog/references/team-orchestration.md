# Team Orchestration Patterns

How agent skills (pm, po, tl) use TeamCreate and Task tools to parallelize backlog-driven work.

## When to Spawn Teams

Agents decide based on workload:

- **Single story / simple task**: Process directly, no team needed.
- **Multiple stories in same phase**: Spawn a team. Each teammate handles a subset of stories.
- **Cross-cutting design/validation**: Spawn a team with specialized agents (dev for implementability, qa for testability).

## Team Patterns by Phase

### Plan Phase (PM leads, PO assists)

PM spawns PO as a teammate to break down objectives into user stories while PM continues gathering requirements.

```mermaid
graph TD
    team["TeamCreate: plan-{project}"]
    team --> pm["pm (leader)<br/><i>gathers requirements, produces PROJECT_BRIEF.md</i>"]
    team --> po["po (teammate)<br/><i>reads brief, creates US via backlog_manager.py</i>"]
```

PO uses `backlog_manager.py create` for each user story. PM reviews the backlog summary when PO finishes.

### Design Phase (TL leads, Dev + QA assist)

TL spawns dev and qa as teammates to review stories in parallel.

```mermaid
graph TD
    team["TeamCreate: design-{project}"]
    team --> tl["tl (leader)<br/><i>produces ARCHITECTURE.md, coordinates</i>"]
    team --> dev["dev (teammate)<br/><i>reviews implementability, flags risks</i>"]
    team --> qa["qa (teammate)<br/><i>reviews testability, flags gaps</i>"]
```

Each teammate reads stories via `backlog_manager.py list --status Ready` and provides feedback. TL updates story statuses to "In Design" as they are processed.

### Validate Phase (PM + TL co-lead)

PM and TL can spawn teammates to validate different aspects in parallel.

```mermaid
graph TD
    team["TeamCreate: validate-{project}"]
    team --> pm["pm (leader)<br/><i>business validation</i>"]
    team --> tl["tl (teammate)<br/><i>technical validation</i>"]
    team --> po["po (teammate)<br/><i>backlog alignment check</i>"]
```

Each validates against the backlog and updates VALIDATION.md with their section.

### Migration (PO or PM leads)

When a project has an existing `docs/BACKLOG.md` in the old markdown format, spawn a migration review team to convert it to the JSON system.

```mermaid
graph TD
    team["TeamCreate: migrate-backlog-{project}"]
    team --> leader["po or pm (leader)<br/><i>coordinates migration, resolves conflicts</i>"]
    team --> reviewer["reviewer (teammate)<br/><i>reads old BACKLOG.md, extracts stories</i>"]
    team --> validator["validator (teammate)<br/><i>compares old vs new, reports discrepancies</i>"]
```

**Reviewer task:** Parse the legacy markdown for US-XXX stories, extracting structured fields (title, role/want/benefit, priority, acceptance criteria, notes, dependencies, feature area). Call `backlog_manager.py create` for each. Preserve original IDs. Migrate open questions via `backlog_manager.py question`.

**Validator task:** After reviewer finishes, run `backlog_manager.py list --format json` and compare against the old file. Report: missing stories, mismatched priorities, lost acceptance criteria, unresolved questions. Produce a structured discrepancy report.

**Leader:** Review the validator's report, fix discrepancies via `backlog_manager.py edit`, render final BACKLOG.md. Inform the user that the old `docs/BACKLOG.md` can be archived.

## Backlog Status Transitions by Phase

| Phase     | Agent  | Status Transition               |
|-----------|--------|--------------------------------|
| Plan      | PO     | → Draft → Ready                |
| Design    | TL     | Ready → In Design              |
| Validate  | PM/TL  | In Design → Validated          |
| Implement | Dev    | Validated → In Progress → In Review |
| Review    | TL     | In Review (stays or → In Progress if issues) |
| Test      | QA     | In Review → In Testing → Done  |

## Task Tool Integration

When a team leader assigns work to teammates, use the Task tools:

1. `TaskCreate` — create a task per user story or group of stories
2. `TaskUpdate` — assign owner, track progress
3. `TaskList` — check team progress

The backlog status and Task status are complementary:
- **Backlog status** = lifecycle stage of the user story across the SDLC
- **Task status** = progress of the current work item within a team session
