"""
agency_cli metrics -- SDLC workflow observability and reporting.

Provides comprehensive metrics on phase timing, gate iterations, and story progress.

Usage:
    agency_cli metrics dashboard --state-path <path>
    agency_cli metrics stories --backlog-path <path> --script-path <path>
    agency_cli metrics phase --state-path <path> --phase <phase>
    agency_cli metrics export --state-path <path> [--backlog-path <path>] [--script-path <path>] --format <json|markdown>
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# Canonical phase sequence (must match state.py)
PHASES = ["plan", "design", "validate", "implement", "review", "test", "document"]
GATE_PHASES = ["validate", "review", "test"]


def _load_state(state_path: str) -> dict:
    """Load STATE.json file."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")

    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration (e.g., '1h 30m 45s')."""
    if seconds is None or seconds < 0:
        return "—"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def _run_backlog_cmd(script_path: str, backlog_path: str, cmd_args: list[str]) -> dict:
    """Execute backlog_manager.py and return parsed JSON output."""
    full_cmd = [sys.executable, script_path] + cmd_args + [backlog_path]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}
        return json.loads(result.stdout) if result.stdout.strip() else {"success": True}
    except json.JSONDecodeError:
        return {"success": True, "output": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 30s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_story_metrics(backlog_path: str, script_path: str) -> dict:
    """Get story metrics by querying the backlog."""
    try:
        # List all stories
        result = _run_backlog_cmd(script_path, backlog_path,
            ["list", "--fields", "id,title,status,priority", "--format", "json"])

        if isinstance(result, dict) and result.get("error"):
            return {
                "error": result.get("error"),
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "completion_rate": 0.0,
                "in_flight": 0,
                "blocked": 0,
            }

        stories = result if isinstance(result, list) else result.get("stories", [])

        # Count by status
        by_status = {}
        by_priority = {}
        in_flight = 0
        blocked = 0

        for story in stories:
            status = story.get("status", "Unknown")
            priority = story.get("priority", "Unknown")

            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

            if status in ("In Progress", "In Review", "In Testing"):
                in_flight += 1
            if status == "Blocked":
                blocked += 1

        total = len(stories)
        done_count = by_status.get("Done", 0)
        completion_rate = (done_count / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "completion_rate": round(completion_rate, 1),
            "in_flight": in_flight,
            "blocked": blocked,
        }
    except Exception as e:
        return {
            "error": str(e),
            "total": 0,
            "by_status": {},
            "by_priority": {},
            "completion_rate": 0.0,
            "in_flight": 0,
            "blocked": 0,
        }


def dashboard(state_path: str) -> dict:
    """Generate comprehensive dashboard from STATE.json."""
    state = _load_state(state_path)

    # Basic project info
    project = state.get("project", "unknown")
    status = state.get("status", "unknown")

    # Progress metrics
    completed_phases = state.get("metrics", {}).get("completed_phases", 0)
    total_phases = state.get("metrics", {}).get("total_phases", len(PHASES))
    progress_pct = (completed_phases / total_phases * 100) if total_phases > 0 else 0.0

    # Timing metrics
    phase_durations = state.get("metrics", {}).get("phase_durations", {})
    total_elapsed_seconds = sum(v for v in phase_durations.values() if isinstance(v, (int, float)))

    # Calculate average and find slowest/fastest
    completed_durations = [v for v in phase_durations.values() if isinstance(v, (int, float)) and v > 0]
    avg_phase_seconds = sum(completed_durations) / len(completed_durations) if completed_durations else 0

    slowest_phase = None
    fastest_phase = None
    if completed_durations:
        slowest_phase = max(phase_durations.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)[0]
        fastest_phase = min((k, v) for k, v in phase_durations.items() if isinstance(v, (int, float)) and v > 0)[0]

    # Estimate remaining time
    remaining_phases = total_phases - completed_phases
    estimated_remaining_seconds = int(avg_phase_seconds * remaining_phases) if avg_phase_seconds > 0 else 0

    # Gate metrics
    total_iterations = state.get("metrics", {}).get("total_gate_iterations", 0)
    by_phase_gates = {}
    first_try_passes = 0
    gate_count = 0

    for phase in GATE_PHASES:
        phase_obj = state.get("phases", {}).get(phase)
        if phase_obj and "gate" in phase_obj:
            gate = phase_obj["gate"]
            iterations = gate.get("iterations", 0)
            verdicts = gate.get("verdicts", [])

            if iterations > 0:
                last_verdict = verdicts[-1] if verdicts else {}
                passed_first_try = iterations == 1

                if phase == "validate":
                    last_verdict_str = last_verdict.get("combined", "UNKNOWN")
                else:
                    last_verdict_str = last_verdict.get("verdict", "UNKNOWN")

                by_phase_gates[phase] = {
                    "iterations": iterations,
                    "last_verdict": last_verdict_str,
                    "passed_first_try": passed_first_try,
                }

                if passed_first_try:
                    first_try_passes += 1
                gate_count += 1

    first_try_pass_rate = (first_try_passes / gate_count * 100) if gate_count > 0 else 0.0

    # Format phase durations
    formatted_phase_durations = {}
    for phase, seconds in phase_durations.items():
        if isinstance(seconds, (int, float)):
            formatted_phase_durations[phase] = {
                "seconds": int(seconds),
                "formatted": _format_duration(int(seconds)),
            }

    return {
        "project": project,
        "status": status,
        "progress": {
            "completed_phases": completed_phases,
            "total_phases": total_phases,
            "percentage": round(progress_pct, 1),
        },
        "timing": {
            "total_elapsed_seconds": int(total_elapsed_seconds),
            "phase_durations": formatted_phase_durations,
            "average_phase_seconds": int(avg_phase_seconds),
            "slowest_phase": slowest_phase,
            "fastest_phase": fastest_phase,
            "estimated_remaining_seconds": estimated_remaining_seconds,
        },
        "gates": {
            "total_iterations": total_iterations,
            "by_phase": by_phase_gates,
            "first_try_pass_rate": round(first_try_pass_rate, 1),
        },
        "stories": {
            "note": "Story metrics require backlog access - use 'metrics stories' subcommand"
        },
    }


def stories(backlog_path: str, script_path: str) -> dict:
    """Generate story-level metrics."""
    return _get_story_metrics(backlog_path, script_path)


def phase(state_path: str, phase_name: str) -> dict:
    """Generate detailed metrics for a specific phase."""
    state = _load_state(state_path)

    phase_name = phase_name.lower().strip()
    if phase_name not in PHASES:
        raise ValueError(f"Invalid phase: {phase_name}. Valid: {', '.join(PHASES)}")

    phase_obj = state.get("phases", {}).get(phase_name, {})

    status = phase_obj.get("status", "unknown")
    duration_seconds = state.get("metrics", {}).get("phase_durations", {}).get(phase_name)
    started_at = phase_obj.get("started_at")
    completed_at = phase_obj.get("completed_at")
    agents = phase_obj.get("agents", {})
    notes = phase_obj.get("notes", "")

    # Gate info
    gate_info = None
    if "gate" in phase_obj:
        gate = phase_obj["gate"]
        iterations = gate.get("iterations", 0)
        verdicts = gate.get("verdicts", [])
        if iterations > 0:
            last_verdict = verdicts[-1] if verdicts else {}
            if phase_name == "validate":
                verdict_str = last_verdict.get("combined", "UNKNOWN")
            else:
                verdict_str = last_verdict.get("verdict", "UNKNOWN")
            gate_info = {
                "iterations": iterations,
                "verdict": verdict_str,
            }

    return {
        "phase": phase_name,
        "status": status,
        "duration_seconds": duration_seconds if isinstance(duration_seconds, (int, float)) else None,
        "duration_formatted": _format_duration(int(duration_seconds)) if isinstance(duration_seconds, (int, float)) else None,
        "started_at": started_at,
        "completed_at": completed_at,
        "agents": agents if agents else None,
        "gate": gate_info,
        "notes": notes if notes else None,
    }


def export_metrics(state_path: str, backlog_path: str = None, script_path: str = None, format_type: str = "json") -> dict | str:
    """Export comprehensive metrics report."""
    if format_type not in ("json", "markdown"):
        raise ValueError(f"Invalid format: {format_type}. Valid: json, markdown")

    # Load dashboard data
    dashboard_data = dashboard(state_path)

    # Load story data if backlog paths provided
    stories_data = None
    if backlog_path and script_path:
        stories_data = _get_story_metrics(backlog_path, script_path)

    if format_type == "json":
        result = {**dashboard_data}
        if stories_data:
            result["stories"] = stories_data
        else:
            result["stories"] = {
                "note": "Story metrics require backlog access - use 'metrics stories' subcommand"
            }
        return result

    else:  # markdown
        return _generate_markdown_report(dashboard_data, stories_data)


def _generate_markdown_report(dashboard_data: dict, stories_data: dict = None) -> str:
    """Generate markdown report from metrics data."""
    lines = []

    # Header
    lines.append("# SDLC Metrics Report\n")
    lines.append(f"**Project:** {dashboard_data.get('project', 'unknown')}")
    lines.append(f"**Status:** {dashboard_data.get('status', 'unknown')} ({dashboard_data.get('progress', {}).get('percentage', 0)}% complete)")
    now = datetime.now(timezone.utc).isoformat()
    lines.append(f"**Generated:** {now}\n")

    # Phase Timing Table
    lines.append("## Phase Timing\n")
    lines.append("| Phase | Status | Duration | Gate |")
    lines.append("|-------|--------|----------|------|")

    for phase in PHASES:
        # This requires reading state again for phase details; we'll build from available data
        status = "unknown"
        duration = "—"
        gate = "—"

        # Try to infer from dashboard data (this is limited, would need state)
        timing = dashboard_data.get("timing", {}).get("phase_durations", {}).get(phase)
        if timing:
            duration = timing.get("formatted", "—")

        lines.append(f"| {phase.capitalize()} | {status} | {duration} | {gate} |")

    lines.append("")

    # Gate Performance
    lines.append("## Gate Performance\n")
    gates = dashboard_data.get("gates", {})
    lines.append(f"- First-try pass rate: {gates.get('first_try_pass_rate', 0)}%")
    lines.append(f"- Total gate iterations: {gates.get('total_iterations', 0)}")

    by_phase = gates.get("by_phase", {})
    for phase_name, gate_info in sorted(by_phase.items()):
        iterations = gate_info.get("iterations", 0)
        verdict = gate_info.get("last_verdict", "UNKNOWN")
        lines.append(f"- {phase_name.capitalize()}: {iterations} iteration(s) ({verdict})")

    lines.append("")

    # Story Progress
    if stories_data and "error" not in stories_data:
        lines.append("## Story Progress\n")
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")

        by_status = stories_data.get("by_status", {})
        for status in sorted(by_status.keys()):
            count = by_status[status]
            lines.append(f"| {status} | {count} |")

        total = stories_data.get("total", 0)
        lines.append(f"| **Total** | **{total}** |")
        lines.append("")

        completion_rate = stories_data.get("completion_rate", 0.0)
        lines.append(f"Completion rate: {completion_rate}%")

        if stories_data.get("in_flight", 0) > 0:
            lines.append(f"In-flight stories: {stories_data.get('in_flight', 0)}")

        if stories_data.get("blocked", 0) > 0:
            lines.append(f"Blocked stories: {stories_data.get('blocked', 0)}")
    else:
        lines.append("## Story Progress\n")
        lines.append("Story metrics not available (backlog not provided).\n")

    # Timing Summary
    lines.append("\n## Timing Summary\n")
    timing = dashboard_data.get("timing", {})
    lines.append(f"- Total elapsed: {_format_duration(timing.get('total_elapsed_seconds', 0))}")
    lines.append(f"- Average phase: {_format_duration(timing.get('average_phase_seconds', 0))}")
    lines.append(f"- Estimated remaining: {_format_duration(timing.get('estimated_remaining_seconds', 0))}")

    return "\n".join(lines)


def handle_metrics(args: list[str]) -> dict | str:
    """Main handler for metrics subcommands."""
    if not args:
        raise ValueError("Subcommand required: dashboard, stories, phase, export")

    subcmd = args[0]

    if subcmd == "dashboard":
        parser = argparse.ArgumentParser(prog="agency_cli metrics dashboard")
        parser.add_argument("--state-path", required=True, help="Path to STATE.json")
        opts = parser.parse_args(args[1:])
        return dashboard(os.path.abspath(opts.state_path))

    elif subcmd == "stories":
        parser = argparse.ArgumentParser(prog="agency_cli metrics stories")
        parser.add_argument("--backlog-path", required=True, help="Path to backlog JSON")
        parser.add_argument("--script-path", required=True, help="Path to backlog_manager.py")
        opts = parser.parse_args(args[1:])
        return stories(os.path.abspath(opts.backlog_path), os.path.abspath(opts.script_path))

    elif subcmd == "phase":
        parser = argparse.ArgumentParser(prog="agency_cli metrics phase")
        parser.add_argument("--state-path", required=True, help="Path to STATE.json")
        parser.add_argument("--phase", required=True, help="Phase name")
        opts = parser.parse_args(args[1:])
        return phase(os.path.abspath(opts.state_path), opts.phase)

    elif subcmd == "export":
        parser = argparse.ArgumentParser(prog="agency_cli metrics export")
        parser.add_argument("--state-path", required=True, help="Path to STATE.json")
        parser.add_argument("--backlog-path", help="Path to backlog JSON (optional)")
        parser.add_argument("--script-path", help="Path to backlog_manager.py (optional)")
        parser.add_argument("--format", required=True, choices=["json", "markdown"],
                          help="Output format: json or markdown")
        opts = parser.parse_args(args[1:])

        backlog_path = os.path.abspath(opts.backlog_path) if opts.backlog_path else None
        script_path = os.path.abspath(opts.script_path) if opts.script_path else None

        return export_metrics(os.path.abspath(opts.state_path), backlog_path, script_path, opts.format)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: dashboard, stories, phase, export")
