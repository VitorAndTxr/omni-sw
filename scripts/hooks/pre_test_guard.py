#!/usr/bin/env python3
"""PreToolUse hook: blocks /qa test if review contains blocking issues.

Prevents testing from starting unless the code review (REVIEW.md) shows
[GATE:PASS] verdict. Blocks if [GATE:FAIL] or no gate verdict is found.
Exit code 2 blocks the tool call and surfaces the stderr message as feedback.
"""

import json
import sys
import os
import re

def find_project_root(current_path):
    """Find project root by looking for agent_docs/agency/STATE.json upward."""
    current = current_path if os.path.isdir(current_path) else os.path.dirname(current_path)
    while current != "/":
        state_path = os.path.join(current, "agent_docs", "agency", "STATE.json")
        if os.path.exists(state_path):
            return current
        current = os.path.dirname(current)
    return None

def is_qa_test_command(command):
    """Check if command is a /qa test invocation."""
    return bool(re.search(r'/qa\s+test', command))

def check_review_gate(project_root):
    """
    Check if REVIEW.md contains [GATE:PASS] marker.
    Returns (passed, reason) tuple.
    """
    review_path = os.path.join(project_root, "docs", "REVIEW.md")

    if not os.path.exists(review_path):
        return False, "REVIEW.md not found"

    try:
        with open(review_path, 'r') as f:
            content = f.read()
    except IOError as e:
        return False, f"Could not read REVIEW.md: {e}"

    # Check for [GATE:PASS] marker (case-insensitive)
    pass_match = re.search(r'\[GATE:\s*PASS\]', content, re.IGNORECASE)
    if pass_match:
        return True, ""

    # Check for [GATE:FAIL] marker
    fail_match = re.search(r'\[GATE:\s*FAIL\]', content, re.IGNORECASE)
    if fail_match:
        return False, "REVIEW.md shows [GATE:FAIL]. Code review failed."

    # Check for blocking issues
    blocking_match = re.search(r'BLOCKING ISSUES', content, re.IGNORECASE)
    if blocking_match:
        return False, "REVIEW.md contains blocking issues that must be fixed."

    # No gate verdict found
    return False, "REVIEW.md does not contain a [GATE:PASS] verdict"

# Main hook logic
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
command = data.get("tool_input", {}).get("command", "")

# Only process Bash commands
if tool_name != "Bash":
    sys.exit(0)

# Only block /qa test commands
if not is_qa_test_command(command):
    sys.exit(0)

# Find project root
project_root = find_project_root(os.getcwd())

# If no project root found, allow
if not project_root:
    sys.exit(0)

# Check review gate status
passed, reason = check_review_gate(project_root)

if not passed:
    print(
        f"BLOCKED: Cannot proceed with /qa test.\n"
        f"Reason: {reason}\n\n"
        "Testing requires code review approval. The code review (REVIEW.md)\n"
        "must be completed and show [GATE:PASS] verdict.\n"
        "Steps:\n"
        "  1. Run /tl review to complete code review\n"
        "  2. Ensure REVIEW.md contains [GATE:PASS]\n"
        "  3. Fix any blocking issues if needed\n"
        "  4. Then proceed with /qa test\n",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
