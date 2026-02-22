# Phase Execution Details

Step-by-step orchestration instructions for each phase. The orchestrator reads this file at initialization alongside `phase-matrix.md`.

## Phase 1: Plan

**Goal:** `docs/PROJECT_BRIEF.md` + backlog.

| Name | Model | Role |
|------|-------|------|
| `pm-plan` | opus | Lead: produce PROJECT_BRIEF.md |
| `po-plan` | sonnet | Lead: create backlog from brief (blocked by pm-plan) |
| `tl-plan-assist` | haiku | Assist: risk notes (parallel with pm-plan) |
| `dev-plan-assist` | haiku | Assist: implementability notes (parallel) |
| `qa-plan-assist` | haiku | Assist: testability notes (parallel) |

1. **Tasks:** "PM: Create PROJECT_BRIEF.md" → `pm-plan`. "PO: Create backlog" → `po-plan` (blocked by PM). TL/Dev/QA assists (optional, parallel with PM).
2. Spawn `pm-plan` (opus) with lead prompt template: invoke `/pm plan`, objective = {OBJECTIVE}.
3. **(Parallel)** Spawn TL/Dev/QA assists (haiku) with assist prompt template.
4. Handle `[QUESTIONS]` → `AskUserQuestion` → relay answers via `SendMessage`.
5. **PO unblocks** after PM completes. Spawn `po-plan` (sonnet): invoke `/po plan`, read PROJECT_BRIEF.md, create backlog.
6. Handle PO questions the same way.
7. **Shutdown** all Phase 1 agents. Report: "Plan complete. Artifacts: PROJECT_BRIEF.md, backlog."

## Phase 2: Design

**Goal:** `docs/ARCHITECTURE.md`.

| Name | Model | Role |
|------|-------|------|
| `tl-design` | opus | Lead: produce ARCHITECTURE.md |
| `dev-design-assist` | haiku | Assist: implementability review (blocked by tl-design) |
| `qa-design-assist` | haiku | Assist: testability review (blocked by tl-design) |

1. **Tasks:** "TL: Create ARCHITECTURE.md" → `tl-design`. Dev/QA assists (blocked by TL, optional).
2. Spawn `tl-design` (opus) with lead prompt template: invoke `/tl design`.
3. Handle TL questions.
4. Once TL completes, spawn `dev-design-assist` and `qa-design-assist` (haiku) in parallel.
5. **Shutdown** all Phase 2 agents. Report: "Design complete. Artifact: ARCHITECTURE.md."

## Phase 3: Validate (GATE)

**Goal:** `docs/VALIDATION.md` with dual verdicts.

| Name | Model | Role |
|------|-------|------|
| `pm-validate` | opus | Lead: business validation |
| `tl-validate` | opus | Lead: technical validation |
| `po-validate-assist` | haiku | Assist: backlog alignment check (optional) |

1. **Tasks:** "PM: Business validation" → `pm-validate`. "TL: Technical validation" → `tl-validate`. PO assist (optional).
2. Spawn `pm-validate` and `tl-validate` (opus) **in parallel** with lead prompt template. Append: "End output with `[VERDICT:APPROVED]` or `[VERDICT:REPROVED]`."
3. **(Parallel)** Spawn `po-validate-assist` (haiku).
4. Monitor `TaskList` until both leads complete. Read `docs/VALIDATION.md`, extract verdicts.
5. **Shutdown** all Phase 3 agents.
6. **Gate:** Both APPROVED → Phase 4. PM REPROVED → loop to Phase 1. TL REPROVED → loop to Phase 2. Escalate after 3 iterations.

## Phase 4: Implement

**Goal:** Source code in `src/`.

| Name | Model | Role |
|------|-------|------|
| `dev-implement` | sonnet | Lead: write production code |
| `tl-implement-assist` | sonnet | Assist: on-demand technical guidance |

TL assist uses Sonnet (not Haiku) — technical guidance requires architecture context depth.

1. **Tasks:** "Dev: Implement approved design" → `dev-implement`. "TL: On-demand guidance" → `tl-implement-assist` (optional).
2. Spawn both (sonnet). Dev with lead prompt template: invoke `/dev implement`. TL with assist prompt template: review ARCHITECTURE.md, wait for questions.
3. Handle Dev questions. If technical, relay to `tl-implement-assist` via `SendMessage`, then relay answer back.
4. **Shutdown** all Phase 4 agents. Report: "Implementation complete."

## Phase 5: Review (GATE)

**Goal:** `docs/REVIEW.md`.

| Name | Model | Role |
|------|-------|------|
| `tl-review` | sonnet | Lead: code review, produce REVIEW.md |
| `qa-review-assist` | haiku | Assist: correctness review (blocked by tl-review) |

1. **Tasks:** "TL: Code review" → `tl-review`. "QA: Correctness review" → `qa-review-assist` (blocked by TL, optional).
2. Spawn `tl-review` (sonnet) with lead prompt template: invoke `/tl review`. Append: "End output with `[GATE:PASS]` or `[GATE:FAIL]`."
3. Once TL completes, spawn `qa-review-assist` (haiku).
4. Read `docs/REVIEW.md`, extract gate status.
5. **Shutdown** all Phase 5 agents.
6. **Gate:** PASS → Phase 6. FAIL → loop to Phase 4. Escalate after 3 iterations.

## Phase 6: Test (GATE)

**Goal:** Tests in `tests/` + `docs/TEST_REPORT.md`.

| Name | Model | Role |
|------|-------|------|
| `qa-test` | sonnet | Lead: write/run tests, produce TEST_REPORT.md |
| `tl-test-assist` | haiku | Assist: coverage review (blocked by qa-test) |

1. **Tasks:** "QA: Write and execute tests" → `qa-test`. "TL: Coverage review" → `tl-test-assist` (blocked by QA, optional).
2. Spawn `qa-test` (sonnet) with lead prompt template: invoke `/qa test`. Append: "End output with `[GATE:PASS]`, `[GATE:FAIL_BUG]`, or `[GATE:FAIL_TEST]`."
3. Once QA completes, spawn `tl-test-assist` (haiku).
4. Read `docs/TEST_REPORT.md`, extract gate status.
5. **Shutdown** all Phase 6 agents.
6. **Gate:** PASS → Phase 7. FAIL_BUG → loop to Phase 4. FAIL_TEST → spawn `qa-test-fix` (sonnet) to fix and re-run. Escalate after 3 iterations.

## Phase 7: Document

**Goal:** All final documentation.

| Name | Model | Role |
|------|-------|------|
| `pm-document` | sonnet | Lead: README.md, CHANGELOG.md |
| `tl-document` | sonnet | Lead: API_REFERENCE.md, ARCHITECTURE.md update |
| `po-document-assist` | haiku | Assist: documentation verification |
| `dev-document-assist` | haiku | Assist: developer documentation |
| `qa-document-assist` | haiku | Assist: test documentation |

1. **Tasks:** "PM: README.md + CHANGELOG.md" → `pm-document`. "TL: API_REFERENCE.md + ARCHITECTURE.md" → `tl-document`. PO/Dev/QA assists (optional).
2. Spawn `pm-document` and `tl-document` (sonnet) **in parallel** with lead prompt template.
3. **(Parallel)** Spawn PO/Dev/QA assists (haiku) with assist prompt template.
4. Monitor `TaskList` until all complete.
5. **Shutdown** all Phase 7 agents. Report: "Documentation complete. SDLC cycle finished."
