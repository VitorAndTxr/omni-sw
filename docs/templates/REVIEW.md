# Code Review

> Phase 5 output — Tech Lead leads, QA Specialist assists.

## Review Summary

**Date:** *YYYY-MM-DD*
**Reviewer:** Tech Lead
**Overall verdict:** PASS / PASS WITH SUGGESTIONS / BLOCKING ISSUES

## Architecture Compliance

| Component | Matches Design | Notes |
|-----------|---------------|-------|
| Project structure | Yes/No | |
| Data models | Yes/No | |
| API contracts | Yes/No | |
| Error handling | Yes/No | |
| Dependency injection | Yes/No | |

## Issues Found

### Blocking Issues (must fix before proceeding)

#### B-001: *[Issue Title]*

- **File:** `path/to/file.cs:line`
- **Severity:** Blocking
- **Category:** Security / Architecture / Correctness / Performance
- **Description:** *What's wrong and why it matters*
- **Recommendation:** *How to fix it*

---

### Suggestions (non-blocking improvements)

#### S-001: *[Suggestion Title]*

- **File:** `path/to/file.cs:line`
- **Category:** Code quality / Convention / Performance
- **Description:** *What could be improved*
- **Recommendation:** *Suggested improvement*

---

## QA Review

**Date:** *YYYY-MM-DD*
**Reviewer:** QA Specialist

### Correctness Assessment

| User Story | Acceptance Criteria Met | Notes |
|-----------|------------------------|-------|
| US-001 | Yes/Partial/No | |
| US-002 | Yes/Partial/No | |

### Edge Cases & Observations

#### Q-001: *[Finding Title]*

- **File:** `path/to/file.cs:line`
- **Severity:** Blocking / Observation
- **Description:** *Edge case or potential issue*
- **Impact:** *What could go wrong*

---

## Convention Adherence

| Convention | Followed | Notes |
|-----------|---------|-------|
| Naming conventions | Yes/No | |
| Error handling pattern | Yes/No | |
| Forbidden patterns avoided | Yes/No | |
| Logging standards | Yes/No | |

## Next Steps

- If blocking issues exist → `/dev implement` to fix, then re-review
- If no blocking issues → `/qa test`
