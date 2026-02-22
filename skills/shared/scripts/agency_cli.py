#!/usr/bin/env python3
"""
agency_cli.py — Unified CLI for deterministic operations in the Software Development Agency.

Eliminates LLM token consumption for operations that follow fixed rules:
path resolution, phase sequencing, model lookup, gate parsing, token analysis, etc.

Usage:
    python agency_cli.py <command> <subcommand> [options]

Commands:
    init        Resolve project paths and initialize environment
    phase       Phase state machine (sequence, next, artifacts)
    gate        Parse gate verdicts from agent output
    agent       Agent config (model lookup, naming, prompt generation, ordering)
    backlog     Batch backlog operations and transition validation
    scan        Repository/project discovery and config extraction
    diagram     Mermaid diagram generation from scan data
    tokens      Token analysis, fragmentation, deduplication
    report      Markdown report generation
"""

import sys
import os

# Add commands directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "commands"))

from commands.init_cmd import handle_init
from commands.phase import handle_phase
from commands.gate import handle_gate
from commands.agent import handle_agent
from commands.backlog_cmd import handle_backlog
from commands.scan import handle_scan
from commands.diagram import handle_diagram
from commands.tokens import handle_tokens
from commands.report import handle_report

COMMANDS = {
    "init": handle_init,
    "phase": handle_phase,
    "gate": handle_gate,
    "agent": handle_agent,
    "backlog": handle_backlog,
    "scan": handle_scan,
    "diagram": handle_diagram,
    "tokens": handle_tokens,
    "report": handle_report,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nCommands:")
        for cmd in COMMANDS:
            print(f"  {cmd}")
        sys.exit(0)

    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Error: Unknown command '{command}'. Available: {', '.join(COMMANDS)}", file=sys.stderr)
        sys.exit(1)

    try:
        result = COMMANDS[command](sys.argv[2:])
        if result is not None:
            if isinstance(result, str):
                print(result)
            else:
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
