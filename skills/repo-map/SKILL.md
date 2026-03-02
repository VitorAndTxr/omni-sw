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

## Agency CLI Integration

This skill uses `agency_cli.py` for deterministic discovery, config extraction, and diagram generation:

Resolve CLI path: find this skill's own SKILL.md via Glob (`**/repo-map/SKILL.md`), then the CLI is at `../shared/scripts/agency_cli.py` relative to the skill directory. Store result as `{CLI}`.

```bash
# Discover repos (replaces manual Glob scanning)
python {CLI} scan discover --root {scan-root}

# Full scan of a single repo (stack, endpoints, DB, env vars)
python {CLI} scan repo --root {repo-path}

# Generate diagrams from scan results
python {CLI} diagram er --input scan-result.json --output docs/database/diagrams.md
python {CLI} diagram endpoints --input scan-result.json --output docs/endpoints.md
python {CLI} diagram service-map --input scan-result.json --output docs/service-map.md
python {CLI} diagram workflow --input scan-result.json --output docs/workflows.md
```

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

2. **Discover and analyze repositories** -- Use the CLI for all deterministic discovery and extraction:
   ```bash
   # Step 2-3: Discover all repos and extract metadata (stack, DB, endpoints, env vars)
   python {CLI} scan discover --root <scan-root>
   # Save output to scan-result.json for diagram generation

   # For deeper analysis of individual repos:
   python {CLI} scan repo --root <repo-path>
   ```

3. **Map cross-project relationships** -- Use LLM judgment for semantic cross-referencing that requires understanding of the codebase context (shared DBs by name matching, inter-service call patterns, shared packages). The CLI provides the raw data; the LLM connects the dots.

4. **Generate diagrams** -- Use the CLI for deterministic diagram scaffolding, then enrich with LLM analysis:
   ```bash
   python {CLI} diagram er --input scan-result.json --output docs/database/diagrams.md
   python {CLI} diagram endpoints --input scan-result.json --output docs/endpoints.md
   python {CLI} diagram service-map --input scan-result.json --output docs/service-map.md
   python {CLI} diagram workflow --input scan-result.json --output docs/workflows.md
   ```
   After generation, review and enrich: add entity details from source code analysis, complete ER diagrams with fields/relationships, add workflow details from business logic inspection.

5. **Write supplementary diagrams in `docs/diagrams/`** -- One file per topic. Use `classDiagram` for domain models, `sequenceDiagram` for multi-step interactions, `flowchart` for conditional business rules. Skip if `workflows.md` already covers everything.

9. **Write `CLAUDE.md`** -- See `references/claude-md-template.md` for structure. Agent memory file at the scan root indexing the entire landscape.

10. **Optimize context** -- After all artifacts are written, invoke the `/apply-progressive-disclosure optimize` skill on the scan root to fragment and optimize the generated `CLAUDE.md` and documentation files for minimal token consumption.

## Diagram Rules

- Use the appropriate Mermaid type: `erDiagram` for data, `sequenceDiagram` for interactions, `flowchart` for logic, `classDiagram` for domain models, `stateDiagram-v2` for state machines.
- Split large diagrams into focused blocks rather than one monolithic graph.
- Label all relationships and transitions.
- Keep entity/node names concise but descriptive.
