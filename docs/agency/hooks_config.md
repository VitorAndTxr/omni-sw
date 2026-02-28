# Blocking Hooks Configuration

This document explains how to register the blocking hook scripts that enforce workflow integrity for the Software Development Agency.

## Overview

Blocking hooks prevent agents from executing phases out of order or without proper gate approvals. They run as `PreToolUse` hooks before Bash commands and use exit code 2 to block tool calls (exit code 0 allows them).

## Blocking Hooks

### 1. phase_sequence_guard.py

**Location:** `scripts/hooks/phase_sequence_guard.py`

**Purpose:** Blocks execution of agent skills (`/pm`, `/po`, `/tl`, `/dev`, `/qa`) if prerequisite phases haven't been completed.

**Blocks:**
- `/design` if `plan` is not completed
- `/validate` if `design` is not completed
- `/implement` if `validate` is not completed OR dual APPROVED verdicts missing
- `/review` if `implement` is not completed
- `/test` if `review` is not completed OR review gate verdict is not PASS
- `/document` if `test` is not completed OR test gate verdict is not PASS

### 2. pre_implement_guard.py

**Location:** `scripts/hooks/pre_implement_guard.py`

**Purpose:** Blocks `/dev implement` if VALIDATION.md doesn't contain dual APPROVED verdicts (PM + TL approval required).

**Checks:**
- Counts `[VERDICT:APPROVED]` markers in `docs/VALIDATION.md`
- Blocks if fewer than 2 APPROVED verdicts found
- Detects REPROVED verdicts and provides feedback

### 3. pre_test_guard.py

**Location:** `scripts/hooks/pre_test_guard.py`

**Purpose:** Blocks `/qa test` if REVIEW.md doesn't show PASS verdict or has blocking issues.

**Checks:**
- Looks for `[GATE:PASS]` marker in `docs/REVIEW.md`
- Blocks if `[GATE:FAIL]` marker found
- Detects "BLOCKING ISSUES" section and provides feedback

### 4. pre_review_guard.py

**Location:** `scripts/hooks/pre_review_guard.py`

**Purpose:** Blocks `/tl review` if there's no source code in `src/` directory.

**Checks:**
- Verifies `src/` directory exists
- Ensures `src/` is not empty (ignores hidden files like `.gitkeep`)
- Provides error if source code not found

## Registration in Claude Code

Hooks are registered in your Claude Code project settings via `.claude/settings.json` or `.claude/hooks.json`.

### Configuration Format

Create or edit `.claude/hooks.json` in your project root:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/hooks/phase_sequence_guard.py",
            "timeout": 10,
            "description": "Enforce phase sequence prerequisites"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_implement_guard.py",
            "timeout": 10,
            "description": "Verify validation approval before implementation"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_test_guard.py",
            "timeout": 10,
            "description": "Verify code review approval before testing"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_review_guard.py",
            "timeout": 10,
            "description": "Verify source code exists before review"
          }
        ]
      }
    ]
  }
}
```

### Setup Steps

1. **Copy the hooks configuration:**
   ```bash
   # Option A: Create new hooks.json file
   cp docs/agency/hooks_config_example.json .claude/hooks.json

   # Option B: Merge with existing settings.json
   cat .claude/hooks.json | jq '.hooks.PreToolUse += [...]' > .claude/hooks.new.json
   mv .claude/hooks.new.json .claude/hooks.json
   ```

2. **Verify hooks directory structure:**
   ```mermaid
   graph TD
       Root["project-root/"]
       Root --> claude[".claude/<br/>hooks.json"]
       Root --> scripts["scripts/hooks/"]
       scripts --> psg["phase_sequence_guard.py"]
       scripts --> pig["pre_implement_guard.py"]
       scripts --> ptg["pre_test_guard.py"]
       scripts --> prg["pre_review_guard.py"]
       Root --> agent["agent_docs/agency/<br/>STATE.json"]
       Root --> docs["docs/"]
       docs --> valid["VALIDATION.md<br/><i>gate verdicts</i>"]
       docs --> review["REVIEW.md<br/><i>review verdicts</i>"]
       Root --> src["src/<br/><i>implementation files</i>"]
   ```

3. **Ensure STATE.json exists:**
   The hooks search for `agent_docs/agency/STATE.json` to track phase completion. If this file doesn't exist, hooks allow execution (first run).

   Template STATE.json:
   ```json
   {
     "phases": {
       "plan": {
         "status": "pending",
         "gate_verdict": ""
       },
       "design": {
         "status": "pending",
         "gate_verdict": ""
       },
       "validate": {
         "status": "pending",
         "gate_verdict": ""
       },
       "implement": {
         "status": "pending",
         "gate_verdict": ""
       },
       "review": {
         "status": "pending",
         "gate_verdict": ""
       },
       "test": {
         "status": "pending",
         "gate_verdict": ""
       },
       "document": {
         "status": "pending",
         "gate_verdict": ""
       }
     }
   }
   ```

## Hook Exit Codes

- **Exit 0:** Tool call proceeds (hook allows the action)
- **Exit 2:** Tool call is blocked (hook surfaces error to stderr)

When a hook exits with code 2, Claude Code displays the stderr message to the user explaining why the action was blocked.

## Graceful Degradation

Hooks are designed to degrade gracefully:

- **If STATE.json doesn't exist:** Allows all phase operations (first run)
- **If VALIDATION.md missing:** Blocks implement (encourages proper workflow)
- **If REVIEW.md missing:** Blocks test (encourages proper workflow)
- **If src/ missing/empty:** Blocks review (encourages implementation first)

## Debugging Hooks

To test a hook manually:

```bash
# Create test input
echo '{
  "tool_name": "Bash",
  "tool_input": {
    "command": "/dev implement"
  }
}' | python scripts/hooks/phase_sequence_guard.py
```

Exit code 2 indicates the hook would block. Exit code 0 indicates it would allow.

## Common Issues

### Issue: Hooks not triggering

**Check:**
1. `.claude/hooks.json` exists in project root
2. Hook paths are correct relative to project root
3. Hook scripts are executable: `chmod +x scripts/hooks/*.py`
4. Python 3 is available in the environment

### Issue: False positives blocking legitimate commands

**Solution:**
- Hooks only block known phase invocation patterns (e.g., `/dev implement`)
- Regular bash commands (`ls`, `git status`, etc.) are not affected
- If a command is incorrectly blocked, the hook name will be in the error message

### Issue: STATE.json not updating

**Solution:**
- The hooks READ state but don't UPDATE it
- A separate STATE.json management script (or agent) must update phase status
- Hooks rely on this external state tracking for decision-making

## Integration with Agency Workflow

The blocking hooks integrate with the Software Development Agency workflow:

1. **Planning Phase** → `/pm plan`
   - No prerequisites
   - Updates STATE.json: `plan.status = "completed"`

2. **Design Phase** → `/tl design`
   - Requires: plan completed
   - Blocked if: plan not completed
   - Updates STATE.json: `design.status = "completed"`

3. **Validation Phase** → `/po validate` and `/tl validate`
   - Requires: design completed
   - Blocked if: design not completed
   - Updates STATE.json: `validate.status = "completed", validate.gate_verdict = "APPROVED,APPROVED"`

4. **Implementation Phase** → `/dev implement`
   - Requires: validation completed + dual APPROVED
   - Blocked by: `phase_sequence_guard.py` and `pre_implement_guard.py`
   - Blocked if: validate gate verdict ≠ "APPROVED,APPROVED" OR VALIDATION.md lacks verdicts
   - Updates STATE.json: `implement.status = "completed"`

5. **Review Phase** → `/tl review`
   - Requires: implementation completed + src/ not empty
   - Blocked by: `pre_review_guard.py`
   - Blocked if: src/ is empty
   - Updates STATE.json: `review.status = "completed", review.gate_verdict = "PASS"`

6. **Test Phase** → `/qa test`
   - Requires: review completed + PASS verdict
   - Blocked by: `phase_sequence_guard.py` and `pre_test_guard.py`
   - Blocked if: review gate verdict ≠ "PASS" OR REVIEW.md lacks PASS marker
   - Updates STATE.json: `test.status = "completed", test.gate_verdict = "PASS"`

7. **Documentation Phase** → `/po document`
   - Requires: test completed + PASS verdict
   - Blocked by: `phase_sequence_guard.py`
   - Blocked if: test gate verdict ≠ "PASS"

## Example .claude/hooks.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/hooks/phase_sequence_guard.py",
            "timeout": 10,
            "description": "Enforce phase sequence prerequisites"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_implement_guard.py",
            "timeout": 10,
            "description": "Verify validation approval before implementation"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_test_guard.py",
            "timeout": 10,
            "description": "Verify code review approval before testing"
          },
          {
            "type": "command",
            "command": "python scripts/hooks/pre_review_guard.py",
            "timeout": 10,
            "description": "Verify source code exists before review"
          }
        ]
      }
    ]
  }
}
```

## Further Reading

- [Hooks System](hooks-system.md) — General hooks system documentation
- [Phase Walkthrough](phase-walkthrough.md) — Complete workflow description
- [Agent Reference](agent-reference.md) — Agent skills reference
