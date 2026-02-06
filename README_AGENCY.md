# Software Development Agency

Multi-agent SDLC workflow built on Claude Code skills. Five role-based agents operate across seven sequential phases, each activated via skill commands (e.g., `/pm plan`, `/tl design`, `/qa test`). The human user orchestrates by invoking agents in order and making gate decisions.

## Role-Phase Matrix

| Agent | Plan | Design | Validate | Implement | Review | Test | Document |
|-------|------|--------|----------|-----------|--------|------|----------|
| PM    | L    | -      | L (biz)  | -         | -      | -    | L (biz)  |
| PO    | A    | -      | A        | -         | -      | -    | A        |
| TL    | A    | L      | L (tech) | A         | L      | A    | L (tech) |
| Dev   | A    | A      | -        | L         | -      | -    | A        |
| QA    | A    | A      | -        | -         | A      | L    | A        |

**L** = Leads. **A** = Assists. **-** = Does not participate.

## Key Design Principles

- Agents are role-constrained (PM never writes code, QA never modifies production code).
- Phases produce concrete artifacts (markdown documents, source code, tests).
- Gate phases (Validate, Review, Test) enforce quality before progression.
- Feedback loops allow iteration without restarting the entire workflow.
- Stack-agnostic; project specifics come from `CLAUDE.md`.

## Documentation Index

Load only docs relevant to the current task.

| Document | When to load |
|----------|-------------|
| `docs/agency/architecture-diagrams.md` | Understanding agent hierarchy, orchestration flow, or feedback loops |
| `docs/agency/agent-reference.md` | Looking up an agent's identity, constraints, phase modes, or outputs |
| `docs/agency/phase-walkthrough.md` | Running a specific phase — step-by-step commands, inputs, outputs, gates |
| `docs/agency/artifact-map.md` | Understanding project directory structure or locating agency files |
| `docs/agency/claude-md-configuration.md` | Configuring a new project's CLAUDE.md for the agency |
| `docs/agency/hooks-system.md` | Adding, modifying, or understanding automated guardrails |
| `docs/agency/templates.md` | Finding or understanding artifact templates |
| `docs/agency/extending-the-agency.md` | Adding new agents, phases, artifacts, or utility skills |
| `docs/agency/known-limitations.md` | Understanding current constraints or planning improvements |
| `docs/agency/file-index.md` | Complete inventory of all agency files |
