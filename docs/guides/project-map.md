# project-map

Discovers all git repositories under a project root, maps each in parallel using [`repo-map`](repo-map.md), and then aggregates the results into project-level documentation: cross-repo service maps, shared database diagrams, and inter-service workflow sequences.

## When to use

- Onboarding to a multi-repository project (monorepo with multiple services, or a project folder containing several independent repos)
- Generating consolidated architecture documentation before starting work
- Understanding cross-service dependencies, shared databases, and integration flows

For a **single repository**, use [`/omni-sw:repo-map`](repo-map.md) directly.

## Invocation

```
/omni-sw:project-map
/omni-sw:project-map /path/to/project-root
```

Without an argument, uses the current working directory as the project root. The skill scans **one level deep** for directories containing a `.git` folder.

## What it produces

### Per-repository (via repo-map)

Each discovered repo gets its own full repo-map output: `CLAUDE.md`, `docs/endpoints.md`, `docs/database/diagrams.md`, `docs/workflows.md`, `docs/diagrams/`.

### Project-level aggregation

Written to the project root `docs/` directory:

| Artifact | Description |
|----------|-------------|
| `CLAUDE.md` | Project-level index with repo inventory, stack summary per service, cross-repo dependencies, env vars, and links to per-repo docs |
| `docs/database/diagrams.md` | Consolidated ER diagrams — shared databases get one canonical diagram listing all consuming services |
| `docs/endpoints.md` | All endpoint catalogs grouped by repository with a summary table |
| `docs/workflows.md` | Cross-repo workflows only (the unique value over individual repo-maps) — auth flows, purchase flows, data sync sequences |
| `docs/diagrams/service-map.md` | Full service map with all repos, databases, and external integrations |
| `docs/diagrams/deployment.md` | Deployment topology (only if Docker/CI config is found) |

## Workflow summary

1. **Discovery** — Scans immediate subdirectories for `.git` folders; skips `docs`, `node_modules`, `.claude`, `agent_docs`.
2. **Parallel mapping** — Launches one `repo-map` Task agent per repository simultaneously (batched at 8 if more repos are found).
3. **Cross-reference analysis** — Identifies shared databases, inter-service HTTP calls, shared packages, Docker Compose service-to-repo mappings, and event/message flows.
4. **Aggregation** — Writes project-level documentation merging all per-repo results.
5. **Optimization** — Runs `/omni-sw:apply-progressive-disclosure optimize` on the project root.

## Constraints

- Read-only: never modifies source code in any repository.
- Backs up any existing `CLAUDE.md` to `CLAUDE.md.bak` before overwriting.
- Redacts DB connection secrets.
- Failed repos are recorded in the "Mapping Gaps" section of the project `CLAUDE.md` and do not abort the run.

## Cross-reference signals detected

| Signal | How detected |
|--------|-------------|
| Shared database | Same DB name or connection key across repos |
| Inter-service calls | HTTP base URLs in one repo matching another repo's API surface |
| Shared packages | NuGet/npm cross-references |
| Docker services | `docker-compose.yml` at project root mapping services to repos |
| Shared auth | Common JWT issuers or OAuth providers |
| Event/message flows | Queue/topic name matching across producers and consumers |

## Tips

- Run once when joining a project — the generated `CLAUDE.md` becomes the entry point for all subsequent agent work.
- If a single repo fails, the rest still complete. Check the "Mapping Gaps" section to see what was skipped and why.
- The project-level `docs/workflows.md` focuses on **cross-service sequences** only; per-service workflows remain in each repo's own docs.
