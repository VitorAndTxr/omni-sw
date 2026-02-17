# Phase-Agent Matrix & Gate Conditions

Quick reference for the orchestrator's phase routing logic.

## Phase → Agent Mapping

| Phase | Lead Agent | Skill Command | Assist Agents (optional) | Output Artifacts |
|-------|-----------|---------------|--------------------------|------------------|
| Plan | PM | `/pm plan` | PO (`/po plan`), TL (`/tl plan`), Dev (`/dev plan`), QA (`/qa plan`) | `docs/PROJECT_BRIEF.md`, backlog |
| Design | TL | `/tl design` | Dev (`/dev design`), QA (`/qa design`) | `docs/ARCHITECTURE.md` |
| Validate | PM + TL | `/pm validate` + `/tl validate` | PO (`/po validate`) | `docs/VALIDATION.md` |
| Implement | Dev | `/dev implement` | TL (`/tl implement`) | Source code in `src/` |
| Review | TL | `/tl review` | QA (`/qa review`) | `docs/REVIEW.md` |
| Test | QA | `/qa test` | TL (`/tl test`) | Tests in `tests/`, `docs/TEST_REPORT.md` |
| Document | PM + TL | `/pm document` + `/tl document` | PO (`/po document`), Dev (`/dev document`), QA (`/qa document`) | `README.md`, `CHANGELOG.md`, `docs/API_REFERENCE.md` |

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
| Test failures (test issue) | QA fixes test internally, re-runs |
| All pass | Proceed to Document |

## Feedback Loop Limits

Maximum 3 iterations per gate before escalating to user with full issue summary.

## Sequential Dependencies Within Phases

- **Plan:** PM must complete PROJECT_BRIEF.md before PO can create backlog. TL/Dev/QA assists can run in parallel after PM.
- **Design:** TL produces ARCHITECTURE.md first. Dev/QA assists review after.
- **Validate:** PM and TL can run in parallel. PO runs after or in parallel.
- **Implement:** Dev leads. TL is on-demand only.
- **Review:** TL first. QA adds section after TL completes.
- **Test:** QA leads. TL reviews after.
- **Document:** PM and TL can run in parallel. PO/Dev/QA after leads complete.
