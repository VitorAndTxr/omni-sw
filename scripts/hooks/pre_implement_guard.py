#!/usr/bin/env python3
"""PreToolUse hook: blocks /dev implement without dual APPROVED validation verdicts.

Prevents implementation from starting unless both PM and TL have approved
the design in VALIDATION.md. Looks for two [VERDICT:APPROVED] markers.
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

def is_dev_implement_command(command):
    """Check if command is a /dev implement invocation."""
    return bool(re.search(r'/dev\s+implement', command))

def check_validation_approved(project_root):
    """
    Check if VALIDATION.md contains two [VERDICT:APPROVED] markers.
    Returns (approved, reason) tuple.
    """
    validation_path = os.path.join(project_root, "docs", "VALIDATION.md")

    if not os.path.exists(validation_path):
        return False, "VALIDATION.md not found"

    try:
        with open(validation_path, 'r') as f:
            content = f.read()
    except IOError as e:
        return False, f"Could not read VALIDATION.md: {e}"

    # Count [VERDICT:APPROVED] markers (case-insensitive)
    approved_matches = re.findall(r'\[VERDICT:\s*APPROVED\]', content, re.IGNORECASE)
    approved_count = len(approved_matches)

    if approved_count >= 2:
        return True, ""

    if approved_count == 1:
        return False, "VALIDATION.md has only 1 APPROVED verdict. Need 2 (PM + TL)"

    # Check for REPROVED or other verdicts
    reproved_matches = re.findall(r'\[VERDICT:\s*REPROVED\]', content, re.IGNORECASE)
    if reproved_matches:
        return False, "VALIDATION.md contains REPROVED verdict(s). Design must be revised."

    return False, "VALIDATION.md does not contain any APPROVED verdicts"

# Main hook logic
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
command = data.get("tool_input", {}).get("command", "")

# Only process Bash commands
if tool_name != "Bash":
    sys.exit(0)

# Only block /dev implement commands
if not is_dev_implement_command(command):
    sys.exit(0)

# Find project root
project_root = find_project_root(os.getcwd())

# If no project root found, allow
if not project_root:
    sys.exit(0)

# Check validation status
approved, reason = check_validation_approved(project_root)

if not approved:
    print(
        f"BLOCKED: Cannot proceed with /dev implement.\n"
        f"Reason: {reason}\n\n"
        "Implementation requires validation approval from both PM and TL.\n"
        "Edit docs/VALIDATION.md and ensure it contains:\n"
        "  1. Business Validation section with [VERDICT:APPROVED]\n"
        "  2. Technical Validation section with [VERDICT:APPROVED]\n"
        "Then return to implementation.\n",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
