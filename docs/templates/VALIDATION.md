# Validation Gate

> Phase 3 output — PM leads business validation, TL leads technical validation.

## Business Validation (Product Manager)

**Date:** *YYYY-MM-DD*
**Verdict:** APPROVED / REPROVED

### Checklist

| # | Criterion | Status | Notes |
|---|----------|--------|-------|
| 1 | All business objectives addressed | Pass/Fail | |
| 2 | Scope boundaries respected | Pass/Fail | |
| 3 | Constraints satisfied | Pass/Fail | |
| 4 | Success criteria achievable | Pass/Fail | |
| 5 | Business risks mitigated | Pass/Fail | |

### Rationale

*Detailed explanation of the verdict. If REPROVED, specify what needs to change.*

### Required Changes (if REPROVED)

- *Change 1: description and which phase to revisit*
- *Next step: `/pm plan` to revise objectives*

---

## Product Owner Review

**Date:** *YYYY-MM-DD*

### Business Rule Compliance

| User Story | Covered in Design | Acceptance Criteria Supported | Notes |
|-----------|-------------------|------------------------------|-------|
| US-001 | Yes/No | Yes/Partial/No | |
| US-002 | Yes/No | Yes/Partial/No | |

### Gaps Identified

- *Gap description and recommendation*

---

## Technical Validation (Tech Lead)

**Date:** *YYYY-MM-DD*
**Verdict:** APPROVED / REPROVED

### Checklist

| # | Criterion | Status | Notes |
|---|----------|--------|-------|
| 1 | Architecture feasible with chosen stack | Pass/Fail | |
| 2 | Scalability concerns addressed | Pass/Fail | |
| 3 | Security risks mitigated | Pass/Fail | |
| 4 | Design is testable | Pass/Fail | |
| 5 | Error scenarios handled | Pass/Fail | |
| 6 | Project structure well-organized | Pass/Fail | |

### Rationale

*Detailed explanation of the verdict. If REPROVED, specify what needs to change.*

### Required Changes (if REPROVED)

- *Change 1: description and what to redesign*
- *Next step: `/tl design` to revise architecture*

---

## Gate Result

| Validation | Verdict | Next Step |
|-----------|---------|-----------|
| Business (PM) | APPROVED / REPROVED | If reproved → `/pm plan` |
| Technical (TL) | APPROVED / REPROVED | If reproved → `/tl design` |

**Proceed to implementation:** Yes / No
