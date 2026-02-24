"""
agency_cli decision -- Decision Log system for design decisions and trade-offs.

Maintains an append-only log of decisions made during the SDLC in docs/DECISIONS.md.
Each decision records the agent role, phase, context, alternatives considered, and impact.

Usage:
    agency_cli decision add --decisions-path <path> --phase <phase> --agent <role> --title <title> --context <context> [--alternatives <text>] [--decision <text>] [--impact <text>]
    agency_cli decision list --decisions-path <path> [--phase <phase>] [--agent <role>]
    agency_cli decision get --decisions-path <path> --id <DEC-XXX>
    agency_cli decision summary --decisions-path <path>
"""

import argparse
import os
from datetime import date
import re


# Valid phases and agents
VALID_PHASES = ["plan", "design", "validate", "implement", "review", "test", "document"]
VALID_AGENTS = ["pm", "po", "tl", "dev", "qa"]


def parse_decisions_markdown(content: str) -> list[dict]:
    """Parse DECISIONS.md content and extract all decisions."""
    decisions = []

    # Split by decision header (## DEC-XXX:)
    pattern = r'^## (DEC-\d+):\s*(.+)$'
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    if not matches:
        return decisions

    for i, match in enumerate(matches):
        dec_id = match.group(1)
        title = match.group(2).strip()

        # Extract the section for this decision
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end].strip()

        decision = {
            "id": dec_id,
            "title": title,
            "phase": None,
            "agent": None,
            "date": None,
            "context": None,
            "alternatives": None,
            "decision": None,
            "impact": None,
            "status": None,
        }

        # Parse metadata lines (- **Key:** value pattern)
        metadata_pattern = r'^-\s+\*\*([^:]+):\*\*\s*(.+)$'
        for line in section.split('\n'):
            line = line.strip()
            meta_match = re.match(metadata_pattern, line)
            if meta_match:
                key = meta_match.group(1).lower()
                value = meta_match.group(2).strip()
                if key in decision:
                    decision[key] = value

        decisions.append(decision)

    return decisions


def get_next_decision_id(decisions: list[dict]) -> str:
    """Generate the next DEC-XXX ID based on existing decisions."""
    if not decisions:
        return "DEC-001"

    # Extract numeric parts and find max
    ids = []
    for dec in decisions:
        match = re.match(r'DEC-(\d+)', dec.get('id', ''))
        if match:
            ids.append(int(match.group(1)))

    if not ids:
        return "DEC-001"

    next_num = max(ids) + 1
    return f"DEC-{next_num:03d}"


def format_decision_table_row(decision: dict) -> str:
    """Format a decision as a markdown table row."""
    return (
        f"| {decision['id']} | {decision['phase']} | {decision['agent']} | "
        f"{decision['title']} | {decision['date']} |"
    )


def format_decision_entry(decision: dict) -> str:
    """Format a decision as a markdown section entry."""
    lines = [
        f"## {decision['id']}: {decision['title']}",
        f"- **Phase:** {decision['phase']}",
        f"- **Agent:** {decision['agent']}",
        f"- **Date:** {decision['date']}",
    ]

    if decision.get('context'):
        lines.append(f"- **Context:** {decision['context']}")

    if decision.get('alternatives'):
        lines.append(f"- **Alternatives considered:** {decision['alternatives']}")

    if decision.get('decision'):
        lines.append(f"- **Decision:** {decision['decision']}")

    if decision.get('impact'):
        lines.append(f"- **Impact:** {decision['impact']}")

    lines.append(f"- **Status:** {decision.get('status', 'Active')}")

    return '\n'.join(lines)


def add_decision(decisions_path: str, phase: str, agent: str, title: str,
                 context: str, alternatives: str = None, decision: str = None,
                 impact: str = None) -> dict:
    """Add a new decision to the DECISIONS.md file."""

    # Validate inputs
    phase = phase.lower()
    agent = agent.lower()

    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase '{phase}'. Valid: {', '.join(VALID_PHASES)}")
    if agent not in VALID_AGENTS:
        raise ValueError(f"Invalid agent '{agent}'. Valid: {', '.join(VALID_AGENTS)}")

    # Read existing decisions if file exists
    if os.path.exists(decisions_path):
        with open(decisions_path, 'r', encoding='utf-8') as f:
            content = f.read()
        existing_decisions = parse_decisions_markdown(content)
    else:
        content = ""
        existing_decisions = []

    # Generate next ID
    next_id = get_next_decision_id(existing_decisions)

    # Create new decision object
    today = date.today().isoformat()
    new_decision = {
        "id": next_id,
        "title": title,
        "phase": phase,
        "agent": agent,
        "date": today,
        "context": context,
        "alternatives": alternatives,
        "decision": decision,
        "impact": impact,
        "status": "Active",
    }

    # Build the new file content
    if not content or not content.strip():
        # Create new file with header
        new_content = "# Decision Log\n\n"
    else:
        new_content = content
        # Ensure we have content before the separator
        if "---" not in new_content:
            new_content += "\n\n---\n\n"

    # Add new row to summary table if it exists
    if "| ID |" in new_content:
        # Find the summary table and add the row before the first "---"
        lines = new_content.split('\n')
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('---'):
                insert_idx = i
                break

        if insert_idx is not None:
            table_row = format_decision_table_row(new_decision)
            lines.insert(insert_idx, table_row)
            new_content = '\n'.join(lines)
    else:
        # Create summary table if it doesn't exist
        table = "| ID | Phase | Agent | Title | Date |\n"
        table += "|-------|-------|-------|-------|------|\n"
        table += format_decision_table_row(new_decision) + "\n"

        # Insert after "# Decision Log" header
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# Decision Log'):
                lines.insert(i + 1, "")
                lines.insert(i + 2, table)
                break
        new_content = '\n'.join(lines)

    # Ensure we have a separator before the detailed entries
    if "---\n\n" not in new_content:
        if new_content.strip() and not new_content.rstrip().endswith("---"):
            new_content += "\n\n---\n\n"

    # Append the full decision entry
    entry = format_decision_entry(new_decision)
    if new_content.rstrip().endswith("---"):
        new_content += "\n\n" + entry
    else:
        new_content += "\n\n" + entry

    # Ensure final newline
    if not new_content.endswith('\n'):
        new_content += '\n'

    # Write to file
    os.makedirs(os.path.dirname(decisions_path) if os.path.dirname(decisions_path) else '.', exist_ok=True)
    with open(decisions_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        "success": True,
        "decision": new_decision,
        "file": decisions_path,
        "message": f"Decision {next_id} added to {decisions_path}",
    }


def list_decisions(decisions_path: str, phase: str = None, agent: str = None) -> dict:
    """List decisions with optional filtering."""
    if not os.path.exists(decisions_path):
        return {"decisions": [], "total": 0, "filters": {"phase": phase, "agent": agent}}

    with open(decisions_path, 'r', encoding='utf-8') as f:
        content = f.read()

    decisions = parse_decisions_markdown(content)

    # Filter if requested
    if phase:
        phase = phase.lower()
        decisions = [d for d in decisions if d['phase'] == phase]

    if agent:
        agent = agent.lower()
        decisions = [d for d in decisions if d['agent'] == agent]

    return {
        "decisions": decisions,
        "total": len(decisions),
        "filters": {"phase": phase, "agent": agent},
    }


def get_decision(decisions_path: str, dec_id: str) -> dict:
    """Get a single decision by ID."""
    if not os.path.exists(decisions_path):
        raise ValueError(f"Decisions file not found: {decisions_path}")

    with open(decisions_path, 'r', encoding='utf-8') as f:
        content = f.read()

    decisions = parse_decisions_markdown(content)

    for decision in decisions:
        if decision['id'].upper() == dec_id.upper():
            return decision

    raise ValueError(f"Decision {dec_id} not found")


def summary_decisions(decisions_path: str) -> dict:
    """Get summary statistics about all decisions."""
    if not os.path.exists(decisions_path):
        return {
            "total": 0,
            "by_phase": {},
            "by_agent": {},
            "latest_id": None,
        }

    with open(decisions_path, 'r', encoding='utf-8') as f:
        content = f.read()

    decisions = parse_decisions_markdown(content)

    # Count by phase and agent
    by_phase = {}
    by_agent = {}

    for decision in decisions:
        phase = decision['phase']
        agent = decision['agent']

        by_phase[phase] = by_phase.get(phase, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1

    # Find latest ID
    latest_id = None
    if decisions:
        latest_id = decisions[-1]['id']

    return {
        "total": len(decisions),
        "by_phase": by_phase,
        "by_agent": by_agent,
        "latest_id": latest_id,
    }


def handle_decision(args: list[str]) -> dict:
    """Main handler for decision commands."""
    if not args:
        raise ValueError("Subcommand required: add, list, get, summary")

    subcmd = args[0]

    if subcmd == "add":
        parser = argparse.ArgumentParser(prog="agency_cli decision add")
        parser.add_argument("--decisions-path", required=True, help="Path to DECISIONS.md")
        parser.add_argument("--phase", required=True, help="Decision phase")
        parser.add_argument("--agent", required=True, help="Agent role")
        parser.add_argument("--title", required=True, help="Decision title")
        parser.add_argument("--context", required=True, help="Decision context")
        parser.add_argument("--alternatives", help="Alternatives considered")
        parser.add_argument("--decision", help="The decision made")
        parser.add_argument("--impact", help="Impact of decision")

        opts = parser.parse_args(args[1:])
        return add_decision(
            opts.decisions_path,
            opts.phase,
            opts.agent,
            opts.title,
            opts.context,
            opts.alternatives,
            opts.decision,
            opts.impact,
        )

    elif subcmd == "list":
        parser = argparse.ArgumentParser(prog="agency_cli decision list")
        parser.add_argument("--decisions-path", required=True, help="Path to DECISIONS.md")
        parser.add_argument("--phase", help="Filter by phase")
        parser.add_argument("--agent", help="Filter by agent role")

        opts = parser.parse_args(args[1:])
        return list_decisions(opts.decisions_path, opts.phase, opts.agent)

    elif subcmd == "get":
        parser = argparse.ArgumentParser(prog="agency_cli decision get")
        parser.add_argument("--decisions-path", required=True, help="Path to DECISIONS.md")
        parser.add_argument("--id", required=True, help="Decision ID (e.g., DEC-001)")

        opts = parser.parse_args(args[1:])
        return get_decision(opts.decisions_path, opts.id)

    elif subcmd == "summary":
        parser = argparse.ArgumentParser(prog="agency_cli decision summary")
        parser.add_argument("--decisions-path", required=True, help="Path to DECISIONS.md")

        opts = parser.parse_args(args[1:])
        return summary_decisions(opts.decisions_path)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: add, list, get, summary")
