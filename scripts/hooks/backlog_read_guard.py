#!/usr/bin/env python3
"""PreToolUse hook: blocks direct Read access to backlog files.

Agents must use backlog_manager.py via Bash instead of reading
backlog.json or BACKLOG.md directly. Exit code 2 blocks the
tool call and surfaces the stderr message as feedback.
"""

import json
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")

blocked = (
    path.endswith("backlog.json") and "agent_docs" in path
) or (
    path.endswith("BACKLOG.md") and "agent_docs" in path
)

if blocked:
    print(
        "BLOCKED: Do not read backlog files directly. "
        "Use backlog_manager.py via Bash instead:\n"
        "  - Stats:   python {script} stats {backlog_path}\n"
        "  - List:    python {script} list {backlog_path} --format summary\n"
        "  - Detail:  python {script} get {backlog_path} --id US-XXX\n"
        "Resolve {script} via Glob: **/backlog/scripts/backlog_manager.py",
        file=sys.stderr,
    )
    sys.exit(2)
