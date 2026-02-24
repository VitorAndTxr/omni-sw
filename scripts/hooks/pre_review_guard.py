#!/usr/bin/env python3
"""PreToolUse hook: blocks /tl review if src/ directory is empty or missing.

Prevents code review from starting unless there is actual source code
to review in the src/ directory. Exit code 2 blocks the tool call and
surfaces the stderr message as feedback.
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

def is_tl_review_command(command):
    """Check if command is a /tl review invocation."""
    return bool(re.search(r'/tl\s+review', command))

def check_src_directory(project_root):
    """
    Check if src/ directory exists and is not empty.
    Returns (has_source, reason) tuple.
    """
    src_path = os.path.join(project_root, "src")

    if not os.path.exists(src_path):
        return False, "src/ directory does not exist"

    if not os.path.isdir(src_path):
        return False, "src/ exists but is not a directory"

    # Check if directory is empty
    try:
        contents = os.listdir(src_path)
    except (IOError, OSError) as e:
        return False, f"Could not read src/ directory: {e}"

    # Filter out common hidden files (like .gitkeep, .DS_Store)
    source_files = [f for f in contents if not f.startswith('.')]

    if not source_files:
        return False, "src/ directory exists but is empty"

    return True, ""

# Main hook logic
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
command = data.get("tool_input", {}).get("command", "")

# Only process Bash commands
if tool_name != "Bash":
    sys.exit(0)

# Only block /tl review commands
if not is_tl_review_command(command):
    sys.exit(0)

# Find project root
project_root = find_project_root(os.getcwd())

# If no project root found, allow
if not project_root:
    sys.exit(0)

# Check src directory
has_source, reason = check_src_directory(project_root)

if not has_source:
    print(
        f"BLOCKED: Cannot proceed with /tl review.\n"
        f"Reason: {reason}\n\n"
        "Code review requires source code to review. The src/ directory\n"
        "must exist and contain implementation files.\n"
        "Steps:\n"
        "  1. Run /dev implement to generate source code\n"
        "  2. Ensure src/ directory contains implementation files\n"
        "  3. Then proceed with /tl review\n",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
