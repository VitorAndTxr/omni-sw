"""
agency_cli backlog — Batch backlog operations and transition validation.

Usage:
    agency_cli backlog validate-transition --from <status> --to <status>
    agency_cli backlog phase-transition --phase <phase> --caller <role> --backlog-path <path> --script-path <path>
    agency_cli backlog batch-create --backlog-path <path> --script-path <path> --caller <role> --input <json-file>
    agency_cli backlog expected-status --phase <phase>
"""

import argparse
import json
import subprocess
import sys

# Valid statuses
STATUSES = [
    "Draft", "Ready", "In Design", "Validated",
    "In Progress", "In Review", "In Testing",
    "Done", "Blocked", "Cancelled"
]

# Valid status transitions (from -> allowed targets)
STATUS_TRANSITIONS = {
    "Draft":       ["Ready", "Cancelled"],
    "Ready":       ["In Design", "Cancelled"],
    "In Design":   ["Validated", "Ready", "Blocked", "Cancelled"],
    "Validated":   ["In Progress", "In Design", "Blocked", "Cancelled"],
    "In Progress": ["In Review", "Validated", "Blocked", "Cancelled"],
    "In Review":   ["In Testing", "In Progress", "Blocked", "Cancelled"],
    "In Testing":  ["Done", "In Progress", "Blocked", "Cancelled"],
    "Done":        [],  # Terminal
    "Blocked":     ["Draft", "Ready", "In Design", "Validated", "In Progress", "In Review", "In Testing", "Cancelled"],
    "Cancelled":   [],  # Terminal
}

# Phase -> expected story status at start/end
PHASE_STATUS_MAP = {
    "plan":      {"from": None,         "to": "Ready",       "agent": "po"},
    "design":    {"from": "Ready",      "to": "In Design",   "agent": "tl"},
    "validate":  {"from": "In Design",  "to": "Validated",   "agent": "tl"},
    "implement": {"from": "Validated",  "to": "In Progress", "agent": "dev"},
    "review":    {"from": "In Progress","to": "In Review",   "agent": "tl"},
    "test":      {"from": "In Review",  "to": "In Testing",  "agent": "qa"},
    "document":  {"from": "In Testing", "to": "Done",        "agent": "pm"},
}

# Permission matrix
PERMISSIONS = {
    "create": ["po", "pm"],
    "edit":   ["po", "pm", "tl"],
    "status": ["po", "pm", "tl", "dev", "qa"],
    "delete": ["po", "pm"],
    "question": ["po", "pm", "tl", "dev", "qa"],
}


def validate_transition(from_status: str, to_status: str) -> dict:
    """Check if a status transition is valid."""
    if from_status not in STATUS_TRANSITIONS:
        return {"valid": False, "error": f"Unknown source status: {from_status}",
                "valid_statuses": STATUSES}

    allowed = STATUS_TRANSITIONS[from_status]
    is_valid = to_status in allowed
    result = {
        "valid": is_valid,
        "from": from_status,
        "to": to_status,
        "allowed_targets": allowed,
    }
    if not is_valid:
        result["error"] = f"Cannot transition from '{from_status}' to '{to_status}'"
    return result


def run_backlog_cmd(script_path: str, backlog_path: str, cmd_args: list[str]) -> dict:
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


def phase_transition(phase: str, caller: str, backlog_path: str, script_path: str) -> dict:
    """Transition all stories from phase-start status to phase-end status, render once."""
    phase = phase.lower()
    if phase not in PHASE_STATUS_MAP:
        raise ValueError(f"Unknown phase: {phase}")

    mapping = PHASE_STATUS_MAP[phase]
    from_status = mapping["from"]
    to_status = mapping["to"]

    if from_status is None:
        return {"skipped": True, "reason": "Plan phase creates stories, no transition needed"}

    # 1. List stories in from_status
    list_result = run_backlog_cmd(script_path, backlog_path,
        ["list", "--status", from_status, "--fields", "id,title,status", "--format", "json"])

    if not isinstance(list_result, list) and not list_result.get("success", True):
        return list_result

    stories = list_result if isinstance(list_result, list) else list_result.get("stories", [])
    if not stories:
        return {"transitioned": 0, "from": from_status, "to": to_status,
                "message": f"No stories in '{from_status}' status"}

    # 2. Transition each story
    results = []
    for story in stories:
        story_id = story.get("id", story) if isinstance(story, dict) else story
        cmd = ["status", "--id", story_id, "--status", to_status, "--caller", caller]
        r = run_backlog_cmd(script_path, backlog_path, cmd)
        results.append({"id": story_id, "result": r})

    # 3. Render once
    render_output = os.path.join(os.path.dirname(backlog_path), "BACKLOG.md")
    run_backlog_cmd(script_path, backlog_path, ["render", "--output", render_output])

    return {
        "transitioned": len(results),
        "from": from_status,
        "to": to_status,
        "results": results,
        "rendered": True,
    }


def batch_create(backlog_path: str, script_path: str, caller: str, input_file: str) -> dict:
    """Create multiple stories from a JSON file, render once at end."""
    with open(input_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)

    if not isinstance(stories, list):
        raise ValueError("Input JSON must be an array of story objects")

    results = []
    for story in stories:
        # Get next ID
        next_id_result = run_backlog_cmd(script_path, backlog_path, ["next-id"])
        story_id = next_id_result.get("id", next_id_result.get("next_id"))

        cmd = ["create", "--id", str(story_id), "--caller", caller]
        for field in ["title", "role", "want", "benefit", "feature", "priority"]:
            if field in story:
                cmd.extend([f"--{field}", str(story[field])])
        if "ac" in story:
            cmd.extend(["--ac", json.dumps(story["ac"])])
        if "depends" in story:
            cmd.extend(["--depends", story["depends"]])

        r = run_backlog_cmd(script_path, backlog_path, cmd)
        results.append({"id": story_id, "result": r})

    # Render once
    render_output = os.path.join(os.path.dirname(backlog_path), "BACKLOG.md")
    run_backlog_cmd(script_path, backlog_path, ["render", "--output", render_output])

    return {
        "created": len(results),
        "results": results,
        "rendered": True,
    }


def handle_backlog(args: list[str]) -> dict:
    if not args:
        raise ValueError("Subcommand required: validate-transition, phase-transition, batch-create, expected-status")

    subcmd = args[0]

    if subcmd == "validate-transition":
        parser = argparse.ArgumentParser(prog="agency_cli backlog validate-transition")
        parser.add_argument("--from", dest="from_status", required=True)
        parser.add_argument("--to", dest="to_status", required=True)
        opts = parser.parse_args(args[1:])
        return validate_transition(opts.from_status, opts.to_status)

    elif subcmd == "phase-transition":
        parser = argparse.ArgumentParser(prog="agency_cli backlog phase-transition")
        parser.add_argument("--phase", required=True)
        parser.add_argument("--caller", required=True)
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        opts = parser.parse_args(args[1:])
        return phase_transition(opts.phase, opts.caller, opts.backlog_path, opts.script_path)

    elif subcmd == "batch-create":
        parser = argparse.ArgumentParser(prog="agency_cli backlog batch-create")
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--caller", required=True)
        parser.add_argument("--input", required=True)
        opts = parser.parse_args(args[1:])
        return batch_create(opts.backlog_path, opts.script_path, opts.caller, opts.input)

    elif subcmd == "expected-status":
        parser = argparse.ArgumentParser(prog="agency_cli backlog expected-status")
        parser.add_argument("--phase", required=True)
        opts = parser.parse_args(args[1:])
        phase = opts.phase.lower()
        if phase not in PHASE_STATUS_MAP:
            raise ValueError(f"Unknown phase: {phase}")
        return PHASE_STATUS_MAP[phase]

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}")
