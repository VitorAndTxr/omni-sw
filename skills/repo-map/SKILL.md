---
name: repo-map
description: >
  Repository discovery and mapping tool that scans a root path, catalogs every project and
  sub-repository, and produces a navigable inventory with Mermaid architecture diagrams.
  Outputs: CLAUDE.md (agent memory), database ER diagrams, API endpoint catalog, workflow
  diagrams, and supplementary class/sequence diagrams. Use when: (1) onboarding to a new
  codebase, (2) inventorying repositories under a directory, (3) generating architecture
  documentation for existing projects, (4) user says "repo-map", "map repos", "discover
  projects", "inventory codebase", "scan repositories".
allowed-tools: Task, TaskOutput, Bash, Glob, Grep, Read, Write, WebFetch, AskUserQuestion, Skill
context: fork
---
# Repository Discovery & Mapping

Read-only codebase analysis skill. Discover every project under a scan root, extract stack/database/API/integration metadata, and produce structured documentation with Mermaid diagrams.

## Variables

- **scan-root**: First argument if provided, otherwise current working directory.
- **output-root**: Same as scan-root. All artifacts are written relative to this path.

## Constraints

- NEVER modify source code in discovered repositories.
- NEVER run or build discovered projects.
- NEVER create CLAUDE.md files inside individual sub-projects.
- All diagrams MUST use Mermaid syntax -- no images, ASCII art, PlantUML, or external tools.
- Redact database connection secrets (keep host/DB name only, strip passwords and user credentials).

## Workflow

Scan and document the codebase in this order:

1. **Read agency context** -- Read `~/.claude/README_AGENCY.md` (if it exists) to understand agency roles, phases, and artifact conventions. Read any existing `CLAUDE.md` at the scan root for project conventions.

2. **Discover repositories** -- Recursively scan `<scan-root>` for project root markers:
   - `.git` directories
   - `.sln` files
   - `package.json` (with `node_modules` excluded)
   - `docker-compose.yml` / `docker-compose.yaml`
   - `*.csproj`, `*.fsproj`
   - `pyproject.toml`, `setup.py`, `requirements.txt`
   - `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`
   Build a flat list: `{name, path, root-marker-type}`.

3. **Analyze each project** -- For every discovered project:
   - **Stack**: runtime (.NET, Node, Python, Go, Rust, Java, etc.), framework, language version.
   - **Entry points**: `Program.cs`, `Startup.cs`, `main.ts`, `index.js`, `main.py`, `main.go`, `docker-compose.yml` services.
   - **Database configs**: connection strings in `appsettings*.json`, `.env`, `docker-compose.yml`; ORM configs (DbContext, Prisma schema, Sequelize models, SQLAlchemy models, migration files).
   - **API surface**: controllers, route definitions, endpoint registrations, minimal API mappings, Express/Fastify routes, OpenAPI/Swagger specs.
   - **External integrations**: HTTP client configs (base URLs, named clients), message broker connections (RabbitMQ, Kafka, Azure Service Bus, MassTransit), queue consumers/producers, gRPC service definitions.
   - **Environment variables**: required env vars from `.env.example`, `appsettings*.json`, `docker-compose.yml`, `launchSettings.json`.

4. **Map cross-project relationships** -- Identify:
   - Shared databases (same connection string or DB name across projects).
   - Inter-service calls (HTTP base URLs pointing to sibling services).
   - Shared packages published from within the repo (NuGet, npm).
   - Docker compose service dependencies.

5. **Write `docs/database/diagrams.md`** -- See `references/database-template.md` for structure. One Mermaid `erDiagram` block per database/schema. Derive entities from EF Core DbContext/entities, Prisma schemas, migration files, or SQL scripts.

6. **Write `docs/endpoints.md`** -- See `references/endpoints-template.md` for structure. Full API catalog per project.

7. **Write `docs/workflows.md`** -- See `references/workflows-template.md` for structure. Use `sequenceDiagram` for cross-service request flows, `flowchart` for business logic branches, `stateDiagram-v2` for entity lifecycle transitions.

8. **Write supplementary diagrams in `docs/diagrams/`** -- One file per topic. Use `classDiagram` for domain models, `sequenceDiagram` for multi-step interactions, `flowchart` for conditional business rules. Skip if `workflows.md` already covers everything.

9. **Write `CLAUDE.md`** -- See `references/claude-md-template.md` for structure. Agent memory file at the scan root indexing the entire landscape.

10. **Optimize context** -- After all artifacts are written, invoke the `/apply-progressive-disclosure optimize` skill on the scan root to fragment and optimize the generated `CLAUDE.md` and documentation files for minimal token consumption.

## Discovery Patterns

### .NET Projects

```
Glob: **/*.sln, **/*.csproj
Entry points: **/Program.cs, **/Startup.cs
DB configs: **/appsettings*.json (ConnectionStrings section), **/Data/*Context.cs
Controllers: **/Controllers/**/*.cs
Integrations: search for IHttpClientFactory, AddHttpClient, IServiceBus, MassTransit
```

### Node/TypeScript Projects

```
Glob: **/package.json (skip node_modules)
Entry points: look at "main"/"scripts.start" in package.json
DB configs: **/.env*, **/prisma/schema.prisma, **/sequelize config
Routes: **/routes/**/*.ts, **/controllers/**/*.ts, Express router files
Integrations: search for axios.create, fetch, amqplib, kafkajs
```

### Python Projects

```
Glob: **/pyproject.toml, **/setup.py, **/requirements.txt
Entry points: **/main.py, **/app.py, **/manage.py
DB configs: **/alembic.ini, **/models.py, **/*_models.py, SQLAlchemy engine configs
Routes: **/routes/**/*.py, FastAPI/Flask route decorators
Integrations: search for httpx, requests.Session, pika, confluent_kafka
```

### Docker Compose

```
Glob: **/docker-compose*.yml, **/docker-compose*.yaml
Extract: service names, images, ports, depends_on, environment variables, volume mounts
Map: which services correspond to which discovered projects (by build context path)
```

## Diagram Rules

- Use the appropriate Mermaid type: `erDiagram` for data, `sequenceDiagram` for interactions, `flowchart` for logic, `classDiagram` for domain models, `stateDiagram-v2` for state machines.
- Split large diagrams into focused blocks rather than one monolithic graph.
- Label all relationships and transitions.
- Keep entity/node names concise but descriptive.
