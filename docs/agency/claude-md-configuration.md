# CLAUDE.md Configuration

How to configure a project for the agency using the `CLAUDE.md` file.

`CLAUDE.md` is the project-level configuration file that all agents read. It sits at the project root and controls stack-specific behavior. To adapt the agency for a new project or technology stack, copy `~/.claude/docs/templates/CLAUDE_TEMPLATE.md` to the project root as `CLAUDE.md` and fill in these sections:

## Sections

**Stack** -- Runtime, framework, ORM, database, infrastructure, testing framework, API documentation tool. Agents use this to specialize their output (e.g., Dev writes C# or TypeScript depending on the runtime, QA uses xUnit or Jest depending on the testing framework).

**Conventions > Naming** -- Defines naming conventions for classes, variables, fields, database tables, and API endpoints. Dev and TL enforce these during implementation and review.

**Conventions > Project Structure** -- Directory layout. Dev follows this when creating files. TL verifies it during review.

**Conventions > Error Handling** -- Pattern for handling expected vs. unexpected failures (e.g., `Result<T>` pattern, `ProblemDetails`). Dev implements, TL reviews.

**Conventions > Logging** -- Logging library and level conventions. Dev implements, TL reviews.

**Domain Glossary** -- Ubiquitous language terms. PM and PO use these when writing business docs. All agents use consistent terminology.

**Forbidden Patterns** -- Anti-patterns to avoid (e.g., no static service classes, no `DateTime.Now`). Dev avoids, TL and QA flag violations.

**Agent Overrides** -- Per-role adjustments for the specific project. These override default agent behavior. For example, "Dev Specialist: Follow vertical slice when the architecture document specifies it" or "QA Specialist: Use xUnit with FluentAssertions; integration tests use WebApplicationFactory."

## How Agents Consume CLAUDE.md

Every agent reads `CLAUDE.md` at the start of its phase mode. The file is referenced in Phase Routing workflows as the first or second step. Agents adapt their behavior based on the stack, conventions, and forbidden patterns defined there. The Agent Overrides section lets you fine-tune specific agent behavior without modifying the skill files.
