---
name: project-map
description: >
  Multi-repository project mapping orchestrator. Discovers all git repositories
  under a project root, maps each in parallel using repo-map, then aggregates into
  project-level documentation with cross-repo service maps, shared database diagrams,
  and inter-service workflow documentation.
  Use when: (1) onboarding to a multi-repo project, (2) user says "project-map",
  "map project", "map all repos", (3) generating architecture documentation for
  a project with multiple repositories.
allowed-tools: Task, TaskOutput, Bash, Glob, Grep, Read, Write, WebFetch, AskUserQuestion, Skill
---
# Multi-Repository Project Mapping

Utility skill (not role-based). Discover all repositories under a project root, map each in parallel via background Task agents invoking `/repo-map`, then aggregate into consolidated project-level documentation.

## Variables

- **project-root**: First argument if provided, otherwise current working directory.
- **output-root**: Same as project-root. All project-level artifacts write here.

## Constraints

- NEVER modify source code in discovered repositories.
- NEVER run or build discovered projects.
- All diagrams MUST use Mermaid syntax.
- Redact database connection secrets (keep host/DB name only, strip passwords and credentials).

## Workflow

### Phase 1 — Discovery (synchronous)

1. **Read agency context** — Read `~/.claude/README_AGENCY.md` (if it exists) to load agency conventions. Read `CLAUDE.md` at project-root (if it exists) for project conventions. Read `docs/PROJECT_BRIEF.md` (if it exists) for domain context.

2. **Discover git repositories** — Scan immediate subdirectories of `<project-root>` for `.git` folders. ONE level deep only. Build list: `{name, path}`. Skip directories named `docs`, `node_modules`, `.claude`, `agent_docs`, `.git`.

3. **Validate discovery** — Zero repos found: abort with a message explaining no repositories were detected. One repo found: suggest `/repo-map` directly, proceed only if user confirms via `AskUserQuestion`.

### Phase 2 — Parallel Repository Mapping (asynchronous)

You MUST launch all Task agents in a single turn by including multiple Task tool calls in one message. Launching them sequentially defeats the purpose of this skill.

4. **Launch ALL Task agents in a single turn** — For each discovered repository, launch a `general-purpose` Task agent with `run_in_background: true`. Read `references/task-agent-prompt-template.md` for the prompt template. Substitute `{{REPO_PATH}}` and `{{REPO_NAME}}` for each repo.

   Each Task agent performs two steps:
   - **Step A**: Invoke `/repo-map` via the Skill tool on the repository
   - **Step B**: Read generated artifacts and write `_repo-map-summary.json` to `<repo>/docs/`

   **Batching rule**: If more than 8 repositories are discovered, launch in batches of 8. Wait for each batch to complete before launching the next.

5. **Monitor completion** — Use `TaskOutput` with `block: false` to poll agents. Check all in a single pass, then wait briefly before polling again. Timeout: 10 minutes per agent.

6. **Collect results** — Read all `_repo-map-summary.json` files in a single turn using multiple Read tool calls. Validate JSON structure. Track failures (missing JSON, malformed data, non-empty errors array).

### Phase 3 — Project-Level Aggregation (synchronous)

Produce project-level documentation mirroring repo-map's artifact structure but at project scope.

7. **Cross-reference analysis** using collected JSON summaries:
   - **Shared databases**: Same DB name or connectionKey across repos
   - **Inter-service calls**: HTTP base URLs matching another repo's API surface
   - **Shared packages**: NuGet/npm cross-references
   - **Docker Compose**: Map services to repos (if compose file exists at project root)
   - **Shared authentication**: Common auth patterns (JWT issuers, OAuth providers)
   - **Event/message flows**: Queue/topic name matching across producers/consumers

8. **Write documentation artifacts** — Write all independent doc files in a single turn using multiple Write tool calls:
   - `docs/database/diagrams.md` — Consolidated ER diagrams. Shared databases get ONE canonical diagram listing all consuming services.
   - `docs/endpoints.md` — All endpoint catalogs grouped by repository. Summary table at top with total endpoints and auth mechanisms per repo.
   - `docs/workflows.md` — **Cross-repo workflows only** (the unique value over individual repo-maps). Sequences spanning multiple services: auth flows, purchase flows, data sync between APIs.
   - `docs/diagrams/service-map.md` — Mermaid `graph` with all services, connections, databases, externals. Use subgraphs per layer (Frontend, APIs, Workers, Data).
   - `docs/diagrams/deployment.md` — Deployment topology if Docker/CI info found. Omit if no deployment info available.

9. **Write `CLAUDE.md`** — Read `references/project-claude-md-template.md` for structure. Back up existing `CLAUDE.md` to `CLAUDE.md.bak` first. The generated CLAUDE.md contains: project overview, repository inventory, service map, stack summary per repo (with links to repo-level docs), cross-repo dependencies, consolidated env vars, conventions, domain glossary, mapping gaps, and documentation index.

10. **Clean up** — Delete all `_repo-map-summary.json` intermediate files from each repo's `docs/` directory.

11. **Optimize context** — Invoke `/apply-progressive-disclosure optimize` on the project root.

## Error Handling

- If a repo's Task agent fails, continue with remaining repos. Record the failure.
- Failed repos appear in the "Mapping Gaps" section of the project CLAUDE.md with the reason.
- If ALL repos fail, abort aggregation and report errors.
- Pre-existing `CLAUDE.md` is backed up to `.bak` before overwrite.
- Pre-existing repo docs are overwritten (idempotent operation).
