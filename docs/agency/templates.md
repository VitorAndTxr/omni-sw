# Templates

Seven artifact templates live in `~/.claude/docs/templates/`. Agents use these as the structure for their output documents. Each template contains section headings, placeholder tables, and guidance comments that the agent fills in with real content.

| Template | File | Phase | Producing Agent | Purpose |
|----------|------|-------|----------------|---------|
| Project Brief | `~/.claude/docs/templates/PROJECT_BRIEF.md` | 1 (Plan) | PM leads | Structured business requirements: objectives, scope, constraints, stakeholders, risks. Includes sections for TL, Dev, and QA specialist notes. |
| Backlog | `~/.claude/docs/templates/BACKLOG.md` | 1 (Plan) | PO produces | User stories with acceptance criteria (Given/When/Then), MoSCoW priority, dependency map (Mermaid), and open questions. |
| Architecture | `~/.claude/docs/templates/ARCHITECTURE.md` | 2 (Design) | TL leads | System overview (Mermaid), tech stack justification, data models (Mermaid ERD), API contracts, component architecture (Mermaid), error handling strategy, security, project structure. |
| Validation | `~/.claude/docs/templates/VALIDATION.md` | 3 (Validate) | PM + TL + PO | Dual gate: business validation checklist (PM), PO business rule compliance review, technical validation checklist (TL), gate result table. |
| Review | `~/.claude/docs/templates/REVIEW.md` | 5 (Review) | TL leads, QA assists | Architecture compliance matrix, blocking issues and suggestions with file references, QA correctness assessment, convention adherence. |
| Test Report | `~/.claude/docs/templates/TEST_REPORT.md` | 6 (Test) | QA leads | Test summary metrics, coverage by user story, unit/integration test results, failure reports with reproduction steps, edge cases tested. |
| API Reference | `~/.claude/docs/templates/API_REFERENCE.md` | 7 (Document) | TL leads | Base URL, authentication, common response formats (including ProblemDetails), endpoint documentation with parameters, request/response examples, validation rules. |

## How Agents Consume Templates

Each skill file's phase mode includes an instruction like "Produce `docs/ARCHITECTURE.md` following the template in `~/.claude/docs/templates/ARCHITECTURE.md`." The agent reads the template, fills in the placeholders with project-specific content, and writes the result to the project's `docs/` directory. Templates stay in `~/.claude/docs/templates/` and are never modified during a project cycle.
