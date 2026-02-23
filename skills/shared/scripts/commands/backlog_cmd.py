"""
agency_cli backlog -- Batch backlog operations and transition validation.

Usage:
    agency_cli backlog validate-transition --from <status> --to <status>
    agency_cli backlog phase-transition --phase <phase> --caller <role> --backlog-path <path> --script-path <path>
    agency_cli backlog batch-create --backlog-path <path> --script-path <path> --caller <role> --input <json-file>
    agency_cli backlog expected-status --phase <phase>
"""

import argparse
import json
import os
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


# Query profiles: predefined field/format combos for common agent needs
QUERY_PROFILES = {
    "minimal":  {"fields": "id,title,status", "format": "summary"},
    "full":     {"fields": None, "format": "json"},
    "audit":    {"fields": None, "format": "json"},  # uses 'get' per story
    "ids":      {"fields": "id", "format": "summary"},
    "ac":       {"fields": "id,title,acceptance_criteria", "format": "json"},
    "progress": {"fields": "id,title,status,priority", "format": "summary"},
}


def query_by_profile(backlog_path: str, script_path: str, phase: str,
                     profile: str, extra_status: str = None) -> dict:
    """Run a predefined backlog query for a phase."""
    phase = phase.lower()
    if profile not in QUERY_PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Valid: {', '.join(QUERY_PROFILES)}")

    # Determine status filter from phase
    if extra_status:
        status = extra_status
    elif phase in PHASE_STATUS_MAP:
        mapping = PHASE_STATUS_MAP[phase]
        status = mapping["from"] if mapping["from"] else None
    else:
        status = None

    prof = QUERY_PROFILES[profile]
    cmd = ["list", backlog_path]
    if status:
        cmd.extend(["--status", status])
    if prof["format"]:
        cmd.extend(["--format", prof["format"]])
    if prof["fields"]:
        cmd.extend(["--fields", prof["fields"]])

    return run_backlog_cmd(script_path, backlog_path, cmd)


def resolve_dependencies(backlog_path: str, script_path: str,
                         story_id: str = None) -> dict:
    """Resolve story dependencies via topological sort."""
    # Get all stories with dependencies
    result = run_backlog_cmd(script_path, backlog_path,
        ["list", "--fields", "id,title,dependencies,status", "--format", "json"])

    stories = result if isinstance(result, list) else result.get("stories", [])
    if not stories:
        return {"ordered": [], "message": "No stories found"}

    # Build dependency graph
    story_map = {}
    deps_graph = {}
    for s in stories:
        sid = s.get("id", "")
        story_map[sid] = s
        raw_deps = s.get("dependencies", "") or ""
        dep_list = [d.strip() for d in raw_deps.split(",") if d.strip()]
        deps_graph[sid] = dep_list

    # If specific story requested, find its full dependency chain
    if story_id:
        if story_id not in story_map:
            raise ValueError(f"Story {story_id} not found")
        # BFS to find all transitive dependencies
        chain = []
        visited = set()
        queue = [story_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            chain.append(current)
            for dep in deps_graph.get(current, []):
                if dep not in visited:
                    queue.append(dep)
        # Reverse so dependencies come first
        chain.reverse()
    else:
        chain = list(deps_graph.keys())

    # Topological sort (Kahn's algorithm)
    in_degree = {sid: 0 for sid in chain}
    for sid in chain:
        for dep in deps_graph.get(sid, []):
            if dep in in_degree:
                in_degree[sid] = in_degree.get(sid, 0) + 1

    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    ordered = []
    while queue:
        queue.sort()  # Deterministic order
        current = queue.pop(0)
        ordered.append(current)
        # Find stories that depend on current
        for sid in chain:
            if current in deps_graph.get(sid, []):
                in_degree[sid] -= 1
                if in_degree[sid] == 0:
                    queue.append(sid)

    # Check for cycles
    has_cycle = len(ordered) != len(chain)

    result_stories = []
    for sid in ordered:
        if sid in story_map:
            result_stories.append({
                "id": sid,
                "title": story_map[sid].get("title", ""),
                "status": story_map[sid].get("status", ""),
                "dependencies": deps_graph.get(sid, []),
            })

    return {
        "ordered": result_stories,
        "count": len(result_stories),
        "has_cycle": has_cycle,
        "cycle_warning": "Circular dependency detected -- some stories could not be ordered" if has_cycle else None,
    }


def handle_backlog(args: list[str]) -> dict:
    if not args:
        raise ValueError("Subcommand required: validate-transition, phase-transition, batch-create, expected-status, query, resolve-dependencies")

    subcmd = args[0]

    if subcmd == "query-profile":
        # Lightweight alias: returns profile config without running backlog_manager
        parser = argparse.ArgumentParser(prog="agency_cli backlog query-profile")
        parser.add_argument("--profile", required=True)
        opts = parser.parse_args(args[1:])
        if opts.profile not in QUERY_PROFILES:
            raise ValueError(f"Unknown profile: {opts.profile}. Valid: {', '.join(QUERY_PROFILES)}")
        return {"profile": opts.profile, **QUERY_PROFILES[opts.profile]}

    elif subcmd == "query":
        parser = argparse.ArgumentParser(prog="agency_cli backlog query")
        parser.add_argument("--phase", required=True)
        parser.add_argument("--profile", required=True, choices=list(QUERY_PROFILES.keys()))
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--status", default=None, help="Override status filter")
        opts = parser.parse_args(args[1:])
        return query_by_profile(opts.backlog_path, opts.script_path, opts.phase, opts.profile, opts.status)

    elif subcmd == "resolve-dependencies":
        parser = argparse.ArgumentParser(prog="agency_cli backlog resolve-dependencies")
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--id", default=None, help="Specific story ID (optional)")
        opts = parser.parse_args(args[1:])
        return resolve_dependencies(opts.backlog_path, opts.script_path, opts.id)

    elif subcmd == "validate-transition":
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
