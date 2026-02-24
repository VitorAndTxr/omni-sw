# Phase-Agent Matrix & Gate Conditions

Quick reference for the orchestrator's phase routing logic and model assignments.

## Phase → Agent Mapping

| Phase | Lead Agent | Lead Model | Skill Command | Assist Agents | Assist Model | Output Artifacts |
|-------|-----------|------------|---------------|---------------|--------------|------------------|
| Plan | PM | opus | `/pm plan` | PO (sonnet), TL/Dev/QA (haiku) | — | `docs/PROJECT_BRIEF.md`, backlog |
| Design | TL | opus | `/tl design` | Dev/QA (haiku) | — | `docs/ARCHITECTURE.md` |
| Validate | PM + TL | opus | `/pm validate` + `/tl validate` | PO (haiku) | — | `docs/VALIDATION.md` |
| Implement | Dev | sonnet | `/dev implement` | TL (sonnet) | — | Source code in `src/` |
| Review | TL | sonnet | `/tl review` | QA (haiku) | — | `docs/REVIEW.md` |
| Test | QA | sonnet | `/qa test` | TL (haiku) | — | Tests in `tests/`, `docs/TEST_REPORT.md` |
| Document | PM + TL | sonnet | `/pm document` + `/tl document` | PO/Dev/QA (haiku) | — | `README.md`, `CHANGELOG.md`, `docs/API_REFERENCE.md` |

## Model Routing

Each agent is spawned with a specific model via the Task tool's `model` parameter. Agents are NOT reused across phases — each phase spawns fresh agents at the optimal model tier and shuts them down before the next phase.

### Model Selection Principles

| Model | Cost | Use For |
|-------|------|---------|
| opus | $15/MTok | Judgment: architecture design, gate verdicts, requirement elicitation |
| sonnet | $3/MTok | Generation: code, stories, reviews, documentation, technical guidance |
| haiku | $0.80/MTok | Lightweight: optional assists, notes, alignment checks |

### Full Agent Matrix

| Phase | Agent Name | Model | Role |
|-------|-----------|-------|------|
| Plan | `pm-plan` | opus | Lead: produce PROJECT_BRIEF.md |
| Plan | `po-plan` | sonnet | Lead: create backlog from brief |
| Plan | `tl-plan-assist` | haiku | Assist: risk notes |
| Plan | `dev-plan-assist` | haiku | Assist: implementability notes |
| Plan | `qa-plan-assist` | haiku | Assist: testability notes |
| Design | `tl-design` | opus | Lead: produce ARCHITECTURE.md |
| Design | `dev-design-assist` | haiku | Assist: implementability review |
| Design | `qa-design-assist` | haiku | Assist: testability review |
| Validate | `pm-validate` | opus | Lead: business validation |
| Validate | `tl-validate` | opus | Lead: technical validation |
| Validate | `po-validate-assist` | haiku | Assist: backlog alignment check |
| Implement | `dev-implement` | sonnet | Lead: write production code |
| Implement | `tl-implement-assist` | sonnet | Assist: on-demand technical guidance |
| Review | `tl-review` | sonnet | Lead: code review |
| Review | `qa-review-assist` | haiku | Assist: correctness review |
| Test | `qa-test` | sonnet | Lead: write/run tests |
| Test | `tl-test-assist` | haiku | Assist: coverage review |
| Document | `pm-document` | sonnet | Lead: README.md, CHANGELOG.md |
| Document | `tl-document` | sonnet | Lead: API_REFERENCE.md, ARCHITECTURE.md update |
| Document | `po-document-assist` | haiku | Assist: documentation verification |
| Document | `dev-document-assist` | haiku | Assist: developer documentation |
| Document | `qa-document-assist` | haiku | Assist: test documentation |

**Summary:** 4 Opus spawns, 7 Sonnet spawns, 11 Haiku spawns.

### Agent Naming Convention

Lead agents:  `{role}-{phase}`           e.g., `pm-plan`, `tl-design`, `dev-implement`
Assists:      `{role}-{phase}-assist`    e.g., `tl-plan-assist`, `qa-review-assist`

### Phase Lifecycle

1. Create tasks via `TaskCreate` (owner = agent name from matrix)
2. Spawn lead agents, then assists in parallel via `Task` with `model` parameter
3. Monitor `TaskList`, handle `[QUESTIONS]` via `AskUserQuestion`
4. Shutdown all phase agents via `SendMessage` (type: `shutdown_request`)
5. Proceed to next phase

## Gate Conditions

### Validate (Dual Gate)

| PM Verdict | TL Verdict | Action |
|-----------|-----------|--------|
| APPROVED | APPROVED | Proceed to Implement |
| REPROVED | any | Return to Plan (`/pm plan`) |
| any | REPROVED | Return to Design (`/tl design`) |

### Review

| Outcome | Action |
|---------|--------|
| Blocking issues found | Return to Implement (`/dev implement`) |
| No blocking issues | Proceed to Test |

### Test

| Outcome | Action |
|---------|--------|
| Bug failures (code issue) | Return to Implement (`/dev implement`), then re-test |
| Test failures (test issue) | Spawn fresh `qa-test-fix` (sonnet) to fix tests, re-run |
| All pass | Proceed to Document |

## Feedback Loop Limits

Maximum 3 iterations per gate before escalating to user with full issue summary. On gate failure, increment the loop counter, shutdown current phase agents, then spawn fresh agents for the target phase using the same model assignments from the matrix.

## Sequential Dependencies Within Phases

- **Plan:** PM must complete PROJECT_BRIEF.md before PO can create backlog. TL/Dev/QA assists can run in parallel after PM.
- **Design:** TL produces ARCHITECTURE.md first. Dev/QA assists review after.
- **Validate:** PM and TL can run in parallel. PO runs after or in parallel.
- **Implement:** Dev leads. TL is on-demand only (both Sonnet for depth).
- **Review:** TL first. QA adds section after TL completes.
- **Test:** QA leads. TL reviews after.
- **Document:** PM and TL can run in parallel. PO/Dev/QA after leads complete.

## Parallel Pipeline Mode

When the backlog contains multiple independent feature areas, the orchestrator can parallelize Implement → Review → Test per feature.

### Pipeline Agent Naming

| Phase | Feature | Lead Name | Assist Name |
|-------|---------|-----------|-------------|
| Implement | auth | `dev-implement-auth` | `tl-implement-auth-assist` |
| Implement | billing | `dev-implement-billing` | `tl-implement-billing-assist` |
| Review | auth | `tl-review-auth` | `qa-review-auth-assist` |
| Test | auth | `qa-test-auth` | `tl-test-auth-assist` |

### Pipeline Model Assignments

Same model tier as standard mode — leads use the matrix model, assists use matrix model.

### Pipeline Prerequisites

- Pipeline mode activates automatically when `pipeline group` returns ≥2 independent groups
- Plan, Design, and Validate always run globally (not per-feature)
- Document always runs globally after all feature pipelines complete
- Stories with cross-feature dependencies go to wave 2

### Incremental Flow

```
Feature A:  Implement ─────→ Review ────→ Test ─────→ ┐
Feature B:  Implement ──→ Review ─→ Test ──→           ├─→ Document
Feature C:        Implement ──────→ Review → Test ───→ ┘
```

Each feature progresses independently through Implement→Review→Test.
Reviews and tests start as soon as their prerequisites are met, not when the full phase completes.
