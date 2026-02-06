# Phase Walkthrough

Detailed step-by-step guide for each of the seven SDLC phases. For authoritative phase-specific agent behavior, see each agent's SKILL.md file.

## Phase 1: Plan

**Purpose:** Establish business objectives, scope, and constraints. Break objectives into actionable user stories.

**Who leads:** PM
**Who assists:** PO, TL, Dev, QA

**Step-by-step:**

1. `/pm plan` -- PM reads `CLAUDE.md` for project context, engages the client in structured conversation, produces `docs/PROJECT_BRIEF.md`.
2. `/po plan` -- PO reads the project brief, breaks objectives into user stories with acceptance criteria (Given/When/Then), produces `docs/BACKLOG.md`.
3. `/tl plan` *(optional)* -- TL adds technical risk assessment (likelihood, impact, mitigation, T-shirt effort) to the brief.
4. `/dev plan` *(optional)* -- Dev adds domain-specific implementation notes.
5. `/qa plan` *(optional)* -- QA adds testability risks and ambiguous acceptance criteria notes.

**Inputs:** `CLAUDE.md`, client conversation.
**Outputs:** `docs/PROJECT_BRIEF.md`, `docs/BACKLOG.md`.
**Gate condition:** PM and PO are satisfied with the brief and backlog. Proceed to Design.

## Phase 2: Design

**Purpose:** Produce a comprehensive architecture document that serves as the implementation blueprint.

**Who leads:** TL
**Who assists:** Dev, QA

**Step-by-step:**

1. `/tl design` -- TL reads the project brief, backlog, and `CLAUDE.md`. Designs system overview, data models, API contracts, component architecture, error handling, security, and project structure. Produces `docs/ARCHITECTURE.md` with Mermaid diagrams.
2. `/dev design` *(optional)* -- Dev reviews for implementability, flags library/framework compatibility issues.
3. `/qa design` *(optional)* -- QA reviews for testability (injectable dependencies, mockable interfaces, clear API contracts).

**Inputs:** `docs/PROJECT_BRIEF.md`, `docs/BACKLOG.md`, `CLAUDE.md`.
**Outputs:** `docs/ARCHITECTURE.md`.
**Gate condition:** Architecture document is complete. Proceed to Validate.

## Phase 3: Validate (Dual Gate)

**Purpose:** Ensure the design satisfies both business and technical requirements before implementation begins.

**Who leads:** PM (business gate), TL (technical gate)
**Who assists:** PO

**Step-by-step:**

1. `/pm validate` -- PM checks architecture against business objectives, scope, and constraints. Produces verdict (APPROVED/REPROVED) in business section of `docs/VALIDATION.md`.
2. `/po validate` *(optional)* -- PO verifies every user story has a path to implementation and acceptance criteria are not contradicted.
3. `/tl validate` -- TL evaluates technical feasibility, scalability, security, testability, error handling. Produces verdict in technical section of `docs/VALIDATION.md`.

**Inputs:** `docs/PROJECT_BRIEF.md`, `docs/ARCHITECTURE.md`, `docs/BACKLOG.md`, `CLAUDE.md`.
**Outputs:** `docs/VALIDATION.md`.

**Gate condition (dual):**

| PM Verdict | TL Verdict | Action |
|-----------|-----------|--------|
| APPROVED | APPROVED | Proceed to Implement |
| REPROVED | any | Return to `/pm plan` |
| any | REPROVED | Return to `/tl design` |

## Phase 4: Implement

**Purpose:** Write production code that faithfully implements the approved architecture.

**Who leads:** Dev
**Who assists:** TL

**Step-by-step:**

1. `/dev implement` -- Dev reads architecture, backlog, validation, conventions from `CLAUDE.md`, and any prior review feedback. Implements data models, business logic, API endpoints, error handling. Produces source code in `src/`.
2. `/tl implement` *(on-demand)* -- TL is available for technical guidance and architecture compliance questions.

**Inputs:** `docs/ARCHITECTURE.md`, `docs/BACKLOG.md`, `docs/VALIDATION.md`, `CLAUDE.md`, `docs/REVIEW.md` (if re-implementing).
**Outputs:** Source code in `src/`.
**Gate condition:** Implementation is complete. Proceed to Review.

## Phase 5: Review

**Purpose:** Structured code review to catch architecture deviations, bugs, security issues, and convention violations before testing.

**Who leads:** TL
**Who assists:** QA

**Step-by-step:**

1. `/tl review` -- TL reviews source code against architecture, backlog criteria, and `CLAUDE.md` conventions. Categorizes issues as **blocking** (must fix) or **suggestion** (nice to have). Produces `docs/REVIEW.md`.
2. `/qa review` *(optional)* -- QA reviews for correctness against acceptance criteria, edge cases, input validation, data integrity. Adds QA section to `docs/REVIEW.md`.

**Inputs:** `docs/ARCHITECTURE.md`, `docs/BACKLOG.md`, `CLAUDE.md`, source code.
**Outputs:** `docs/REVIEW.md`.

**Gate condition:**

| Outcome | Action |
|---------|--------|
| Blocking issues found | Return to `/dev implement` to fix, then re-review |
| No blocking issues | Proceed to Test |

## Phase 6: Test

**Purpose:** Verify the implementation meets acceptance criteria through unit and integration tests.

**Who leads:** QA
**Who assists:** TL

**Step-by-step:**

1. `/qa test` -- QA reads backlog (acceptance criteria drive test cases), architecture (system structure for integration tests), review findings, and `CLAUDE.md` (test framework conventions). Creates unit tests, integration tests, and edge case tests in `tests/`. Executes test suite. Produces `docs/TEST_REPORT.md`.
2. `/tl test` *(optional)* -- TL reviews test coverage adequacy and strategy.

**Inputs:** `docs/BACKLOG.md`, `docs/ARCHITECTURE.md`, `docs/REVIEW.md`, `CLAUDE.md`, source code.
**Outputs:** Test files in `tests/`, `docs/TEST_REPORT.md`.

**Gate condition:**

| Outcome | Action |
|---------|--------|
| Test failures (bugs in code) | Return to `/dev implement` to fix, then `/qa test` |
| Test failures (test issue) | QA fixes test, re-runs |
| All pass | Proceed to Document |

## Phase 7: Document

**Purpose:** Produce all project documentation for end users, stakeholders, and developers.

**Who leads:** PM (business), TL (technical)
**Who assists:** PO, Dev, QA

**Step-by-step:**

1. `/pm document` -- PM produces `README.md` (project overview, setup, usage) and `CHANGELOG.md`.
2. `/tl document` -- TL produces `docs/API_REFERENCE.md` and updates `docs/ARCHITECTURE.md` to reflect implementation changes.
3. `/po document` *(optional)* -- PO reviews business docs for accuracy against backlog.
4. `/dev document` *(optional)* -- Dev adds inline code documentation (XML doc comments, JSDoc).
5. `/qa document` *(optional)* -- QA finalizes test documentation, adds testing section to README.

**Inputs:** All `docs/*.md` files, source code, test files, `CLAUDE.md`.
**Outputs:** `README.md`, `CHANGELOG.md`, `docs/API_REFERENCE.md`, updated `docs/ARCHITECTURE.md`.
**Gate condition:** All documentation complete. Project cycle is finished.
