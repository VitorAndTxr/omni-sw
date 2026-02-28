# repo-map

Scans a repository and produces architecture documentation: a `CLAUDE.md` index, database ER diagrams, API endpoint catalog, service map, and workflow diagrams — all in Mermaid syntax.

## When to use

- Onboarding to an unfamiliar codebase
- Generating architecture docs for an existing project before starting SDLC phases
- Building the context that agents will read during Plan and Design

For projects with **multiple repositories**, use [`/omni-sw:project-map`](project-map.md) instead — it calls repo-map in parallel per repo and then aggregates.

## Invocation

```
/omni-sw:repo-map
/omni-sw:repo-map /path/to/repo
```

Without an argument, scans the current working directory.

## What it produces

All artifacts are written relative to the scan root.

| Artifact | Description |
|----------|-------------|
| `CLAUDE.md` | Agent memory index — stack, conventions, endpoints, dependencies, doc links |
| `docs/database/diagrams.md` | ER diagrams (`erDiagram`) for all detected databases |
| `docs/endpoints.md` | API endpoint catalog grouped by controller/router |
| `docs/diagrams/service-map.md` | Mermaid service map with external integrations |
| `docs/workflows.md` | Business workflow diagrams derived from business logic |
| `docs/diagrams/` | Supplementary class and sequence diagrams (generated as needed) |

## Workflow summary

1. Reads any existing `CLAUDE.md` for project conventions.
2. Runs `agency_cli.py scan discover` to find all sub-repos and `scan repo` to extract metadata (stack, DB schemas, endpoints, env vars).
3. Cross-references shared databases, inter-service calls, and shared packages using LLM analysis.
4. Generates all diagram files via CLI, then enriches them with source code analysis.
5. Writes `CLAUDE.md` with the full landscape index.
6. Automatically runs `/omni-sw:apply-progressive-disclosure optimize` to minimize token cost of the generated files.

## Constraints

- Read-only: never modifies source code.
- Never runs or builds the scanned project.
- Redacts DB connection secrets — keeps host and database name, strips passwords and credentials.
- All diagrams use Mermaid syntax (no images, PlantUML, or ASCII art).

## Example output (CLAUDE.md excerpt)

```markdown
## Stack
- Runtime: .NET 8 / ASP.NET Core
- Database: PostgreSQL (EF Core)
- Auth: JWT Bearer

## API Endpoints
See docs/endpoints.md — 34 endpoints across 6 controllers.

## Databases
See docs/database/diagrams.md — 2 schemas: orders, identity.
```

## Tips

- Run before `/omni-sw:pm plan` so the PM agent has architecture context from the start.
- If the scan root already has a `CLAUDE.md`, repo-map reads it first and preserves any existing conventions.
- Large repos with many services may take a few minutes; the skill parallelizes what it can via the CLI.
