# Test Report

> Phase 6 output — QA Specialist leads, Tech Lead assists.

## Test Summary

**Date:** *YYYY-MM-DD*
**Framework:** *e.g., xUnit + FluentAssertions*
**Overall result:** PASS / FAIL

| Metric | Value |
|--------|-------|
| Total tests | 0 |
| Passed | 0 |
| Failed | 0 |
| Skipped | 0 |

## Test Coverage by User Story

| User Story | Unit Tests | Integration Tests | Status |
|-----------|-----------|------------------|--------|
| US-001 | *count* | *count* | Pass/Fail |
| US-002 | *count* | *count* | Pass/Fail |

## Unit Tests

### *[Service/Component Name]*

| Test | Description | Result | Notes |
|------|-----------|--------|-------|
| `Should_DoX_When_Y` | *What it validates* | Pass/Fail | |
| `Should_DoA_When_B` | *What it validates* | Pass/Fail | |

## Integration Tests

### *[Endpoint / Feature]*

| Test | Description | Result | Notes |
|------|-----------|--------|-------|
| `GET /api/resource returns 200` | *What it validates* | Pass/Fail | |
| `POST /api/resource returns 400 for invalid input` | *What it validates* | Pass/Fail | |

## Failures

### F-001: *[Failure Title]*

- **Test:** `TestClass.TestMethod`
- **Type:** Bug / Test Issue
- **Expected:** *Expected behavior*
- **Actual:** *Actual behavior*
- **Reproduction:** *Steps or input to reproduce*
- **Root cause:** *If identified*
- **Action:** Fix in `/dev implement` / Fix test

---

## Edge Cases Tested

| # | Scenario | Covered | Test |
|---|---------|---------|------|
| 1 | Null input | Yes/No | `TestName` |
| 2 | Empty collection | Yes/No | `TestName` |
| 3 | Max length values | Yes/No | `TestName` |
| 4 | Concurrent access | Yes/No | `TestName` |

## Next Steps

- If failures of type **Bug** → `/dev implement` to fix, then `/qa test` to re-test
- If all pass → `/pm document` and `/tl document`
