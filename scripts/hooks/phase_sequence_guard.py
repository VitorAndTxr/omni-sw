#!/usr/bin/env python3
"""PreToolUse hook: blocks agent skill invocations that violate phase sequence.

Agents must complete prerequisite phases before proceeding to the next phase.
Checks STATE.json to verify phase dependencies are satisfied. Exit code 2
blocks the tool call and surfaces the stderr message as feedback.

Phase sequence rules:
  - plan: always allowed
  - design: plan must be "completed"
  - validate: design must be "completed"
  - implement: validate must be "completed" AND last validate gate verdict must be "APPROVED,APPROVED"
  - review: implement must be "completed"
  - test: review must be "completed" AND last review gate verdict must be "PASS"
  - document: test must be "completed" AND last test gate verdict must be "PASS"
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

def detect_phase_from_command(command):
    """
    Detect phase invocation from bash command.
    Looks for patterns like:
      - /dev implement
      - /pm plan
      - /tl design
      - /qa test
      - --phase implement
    Returns (skill, phase) or (None, None) if not detected.
    """
    # Pattern 1: Direct slash commands like "/dev implement"
    slash_match = re.search(r'/(?:pm|po|tl|dev|qa)\s+(\w+)', command)
    if slash_match:
        phase = slash_match.group(1)
        skill_match = re.search(r'/(\w+)', command)
        if skill_match:
            skill = skill_match.group(1)
            return skill, phase

    # Pattern 2: Look for --phase argument
    phase_match = re.search(r'--phase\s+(\w+)', command)
    if phase_match:
        phase = phase_match.group(1)
        # Try to infer skill from other patterns
        for skill in ['pm', 'po', 'tl', 'dev', 'qa']:
            if skill in command:
                return skill, phase
        return None, phase

    return None, None

def can_proceed(phase, state_data):
    """
    Check if a phase can proceed based on STATE.json data.
    Returns (allowed, reason) tuple.
    """
    if not state_data:
        # If STATE.json doesn't exist or is empty, allow (first run)
        return True, ""

    phases = state_data.get("phases", {})

    # plan is always allowed
    if phase == "plan":
        return True, ""

    # design requires plan to be completed
    if phase == "design":
        plan_status = phases.get("plan", {}).get("status")
        if plan_status != "completed":
            return False, f"Design requires plan to be completed. Current plan status: {plan_status}"
        return True, ""

    # validate requires design to be completed
    if phase == "validate":
        design_status = phases.get("design", {}).get("status")
        if design_status != "completed":
            return False, f"Validate requires design to be completed. Current design status: {design_status}"
        return True, ""

    # implement requires validate to be completed AND dual APPROVED verdicts
    if phase == "implement":
        validate_status = phases.get("validate", {}).get("status")
        if validate_status != "completed":
            return False, f"Implement requires validate to be completed. Current validate status: {validate_status}"

        # Check for dual APPROVED verdicts in last validate gate
        validate_gate = phases.get("validate", {}).get("gate_verdict", "")
        if validate_gate != "APPROVED,APPROVED":
            return False, f"Implement requires dual APPROVED verdicts from validation gate. Current verdict: {validate_gate}"
        return True, ""

    # review requires implement to be completed
    if phase == "review":
        implement_status = phases.get("implement", {}).get("status")
        if implement_status != "completed":
            return False, f"Review requires implement to be completed. Current implement status: {implement_status}"
        return True, ""

    # test requires review to be completed AND PASS verdict
    if phase == "test":
        review_status = phases.get("review", {}).get("status")
        if review_status != "completed":
            return False, f"Test requires review to be completed. Current review status: {review_status}"

        review_gate = phases.get("review", {}).get("gate_verdict", "")
        if review_gate != "PASS":
            return False, f"Test requires PASS verdict from review gate. Current verdict: {review_gate}"
        return True, ""

    # document requires test to be completed AND PASS verdict
    if phase == "document":
        test_status = phases.get("test", {}).get("status")
        if test_status != "completed":
            return False, f"Document requires test to be completed. Current test status: {test_status}"

        test_gate = phases.get("test", {}).get("gate_verdict", "")
        if test_gate != "PASS":
            return False, f"Document requires PASS verdict from test gate. Current verdict: {test_gate}"
        return True, ""

    # Unknown phase, allow by default
    return True, ""

# Main hook logic
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
command = data.get("tool_input", {}).get("command", "")

# Only process Bash commands
if tool_name != "Bash":
    sys.exit(0)

# Detect if this is a phase invocation
skill, phase = detect_phase_from_command(command)

# If not a phase invocation, allow
if not phase:
    sys.exit(0)

# Try to find project root to locate STATE.json
# Start from current working directory or use a heuristic
project_root = find_project_root(os.getcwd())

# If no project root found, allow (first run or setup phase)
if not project_root:
    sys.exit(0)

# Load STATE.json if it exists
state_path = os.path.join(project_root, "agent_docs", "agency", "STATE.json")
state_data = {}
if os.path.exists(state_path):
    try:
        with open(state_path, 'r') as f:
            state_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        # If STATE.json is malformed, allow
        sys.exit(0)

# Check if phase can proceed
allowed, reason = can_proceed(phase, state_data)

if not allowed:
    print(
        f"BLOCKED: Cannot proceed with '{phase}' phase.\n"
        f"Reason: {reason}\n\n"
        "Phase sequence rules:\n"
        "  - plan: always allowed\n"
        "  - design: plan must be 'completed'\n"
        "  - validate: design must be 'completed'\n"
        "  - implement: validate must be 'completed' + dual APPROVED verdicts\n"
        "  - review: implement must be 'completed'\n"
        "  - test: review must be 'completed' + PASS verdict\n"
        "  - document: test must be 'completed' + PASS verdict\n",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
