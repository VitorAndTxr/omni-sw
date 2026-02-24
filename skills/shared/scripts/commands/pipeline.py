"""
agency_cli pipeline -- Feature-based parallel execution pipelines.

Enables grouping stories by feature area into independent pipelines that can execute
in parallel, respecting inter-feature dependencies.

Usage:
    agency_cli pipeline group --backlog-path <path> --script-path <path> [--status <status>]
    agency_cli pipeline agents --phase <phase> --feature <feature> --project-root <path> --script-path <path> --backlog-path <path> --objective <text>
    agency_cli pipeline status --state-path <path>
    agency_cli pipeline ready-for --backlog-path <path> --script-path <path> --phase <review|test>
"""

import argparse
import json
import os
import sys

from backlog_cmd import run_backlog_cmd, PHASE_STATUS_MAP
from agent import (
    AGENT_MATRIX, PHASE_ORDER, validate_phase, validate_role,
    get_agent_name, get_model, generate_prompt
)


def _load_json_file(filepath: str) -> dict:
    """Load and parse a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _get_feature_branch_name(feature_area: str) -> str:
    """Generate a branch name from feature area."""
    # Normalize to lowercase and replace spaces with hyphens
    return f"feat/{feature_area.lower().replace(' ', '-')}"


def _extract_dependencies(story: dict) -> list[str]:
    """Extract dependency list from a story dict."""
    deps = story.get("dependencies", "") or ""
    if isinstance(deps, str):
        return [d.strip() for d in deps.split(",") if d.strip()]
    elif isinstance(deps, list):
        return deps
    return []


def pipeline_group(backlog_path: str, script_path: str, status: str = "Validated") -> dict:
    """
    Group stories by feature_area into independent pipelines, respecting dependencies.

    Logic:
    1. Query stories with given status
    2. Group by feature_area field
    3. For each group, check if any story has dependencies on stories in OTHER groups
    4. Dependent groups go to wave 2, independent groups to wave 1
    """
    # Query stories with the given status
    result = run_backlog_cmd(script_path, backlog_path,
        ["list", "--status", status, "--fields", "id,title,feature_area,dependencies,status", "--format", "json"])

    stories = result if isinstance(result, list) else result.get("stories", [])
    if not stories:
        return {
            "waves": [],
            "total_groups": 0,
            "total_stories": 0,
            "parallelizable_groups": 0,
            "message": f"No stories found with status '{status}'"
        }

    # Build story map and dependency graph
    story_map = {}
    for story in stories:
        story_id = story.get("id", "")
        story_map[story_id] = story

    # Group stories by feature_area
    groups_by_feature = {}
    for story in stories:
        feature = story.get("feature_area", "unclassified")
        if feature not in groups_by_feature:
            groups_by_feature[feature] = []
        groups_by_feature[feature].append(story)

    # Build dependency relationships
    feature_deps = {}  # feature -> set of features it depends on
    for feature, feature_stories in groups_by_feature.items():
        feature_deps[feature] = set()
        for story in feature_stories:
            deps = _extract_dependencies(story)
            for dep_id in deps:
                if dep_id in story_map:
                    dep_feature = story_map[dep_id].get("feature_area", "unclassified")
                    if dep_feature != feature:
                        # This feature depends on another feature
                        feature_deps[feature].add(dep_feature)

    # Determine waves using topological sort
    # Wave 1: features with no dependencies on other features
    # Wave 2+: features that depend on earlier waves
    wave_assignment = {}
    processed = set()
    current_wave = 1

    while len(processed) < len(groups_by_feature):
        wave_features = []
        for feature in groups_by_feature:
            if feature in processed:
                continue
            # Check if all dependencies are processed
            deps_ready = all(dep in processed for dep in feature_deps[feature])
            if deps_ready:
                wave_features.append(feature)

        if not wave_features:
            # Cycle detection: remaining features form a cycle
            break

        for feature in wave_features:
            wave_assignment[feature] = current_wave
            processed.add(feature)

        current_wave += 1

    # Build wave structures
    waves_dict = {}
    for feature, wave_num in wave_assignment.items():
        if wave_num not in waves_dict:
            waves_dict[wave_num] = []

        group = {
            "feature_area": feature,
            "stories": [s.get("id", "") for s in groups_by_feature[feature]],
            "branch_name": _get_feature_branch_name(feature),
            "can_parallel": True,
        }

        # If this feature has dependencies, note them
        if feature_deps[feature]:
            depends_on_features = [f for f in feature_deps[feature] if f in wave_assignment]
            if depends_on_features:
                group["depends_on"] = [_get_feature_branch_name(f) for f in depends_on_features]
                group["can_parallel"] = False

        waves_dict[wave_num].append(group)

    # Build output
    waves = []
    for wave_num in sorted(waves_dict.keys()):
        waves.append({
            "wave": wave_num,
            "groups": waves_dict[wave_num],
        })

    # Count parallelizable groups (groups with can_parallel=true)
    parallelizable = sum(1 for wave in waves for group in wave.get("groups", []) if group.get("can_parallel", False))

    return {
        "waves": waves,
        "total_groups": len(groups_by_feature),
        "total_stories": len(stories),
        "parallelizable_groups": parallelizable,
    }


def pipeline_agents(phase: str, feature_area: str, project_root: str, script_path: str,
                   backlog_path: str, objective: str) -> dict:
    """
    Return agent configuration for a single feature pipeline phase.

    Gets agents for the phase, filters to those relevant for this feature,
    and generates feature-scoped prompts.
    """
    phase = validate_phase(phase)

    # Query stories for this feature in the appropriate status for this phase
    from_status = PHASE_STATUS_MAP.get(phase, {}).get("from")

    stories_result = []
    if from_status:
        result = run_backlog_cmd(script_path, backlog_path,
            ["list", "--status", from_status, "--fields", "id,title,feature_area", "--format", "json"])
        all_stories = result if isinstance(result, list) else result.get("stories", [])
        # Filter to just this feature
        stories_result = [s for s in all_stories if s.get("feature_area", "") == feature_area]

    story_ids = [s.get("id", "") for s in stories_result]

    # Build feature-scoped objective
    feature_objective = objective
    if feature_area:
        feature_objective = f"{objective} (Feature: {feature_area})"

    # Get agents for this phase
    agents = []

    # Determine which roles are active in this phase
    phase_order = PHASE_ORDER.get(phase.lower(), [])
    phase_roles = set()
    for wave in phase_order:
        for role in wave:
            phase_roles.add(role)

    # Build agents for each role in this phase
    for role in sorted(phase_roles):
        key = (phase, role)
        if key not in AGENT_MATRIX:
            continue

        info = AGENT_MATRIX[key]
        agent_type = info["type"]

        # Generate agent name with feature
        if agent_type == "assist":
            agent_name = f"{role}-{phase}-{feature_area.replace(' ', '-').lower()}-assist"
        else:
            agent_name = f"{role}-{phase}-{feature_area.replace(' ', '-').lower()}"

        # Generate feature-scoped prompt
        prompt = generate_prompt(
            role, phase, project_root, script_path, backlog_path,
            feature_objective, agent_type
        )

        agents.append({
            "name": agent_name,
            "role": role,
            "model": info["model"],
            "type": agent_type,
            "prompt": prompt,
            "stories": story_ids,
        })

    return {
        "feature": feature_area,
        "phase": phase,
        "agents": agents,
    }


def pipeline_status(state_path: str) -> dict:
    """
    Return status of all active pipelines from STATE.json.

    Checks if 'pipelines' key exists in the implement phase and returns
    status of each pipeline.
    """
    state = _load_json_file(state_path)

    pipelines = []

    # Check implement phase for pipelines
    implement_phase = state.get("phases", {}).get("implement", {})
    phase_pipelines = implement_phase.get("pipelines", [])

    if isinstance(phase_pipelines, list):
        for pipeline in phase_pipelines:
            if isinstance(pipeline, dict):
                pipelines.append({
                    "feature": pipeline.get("feature", ""),
                    "phase": pipeline.get("phase", "implement"),
                    "status": pipeline.get("status", "unknown"),
                })

    # Check if all pipelines are completed
    all_completed = all(p.get("status") == "completed" for p in pipelines) if pipelines else False

    return {
        "pipelines": pipelines,
        "all_completed": all_completed,
    }


def pipeline_ready_for(backlog_path: str, script_path: str, phase: str) -> dict:
    """
    Return stories ready for the next phase based on status.

    - For 'review': returns stories in "In Progress" status
    - For 'test': returns stories in "In Review" status
    Groups them by feature_area.
    """
    phase = phase.lower()

    if phase == "review":
        # Looking for stories ready to be reviewed (in progress)
        ready_status = "In Progress"
    elif phase == "test":
        # Looking for stories ready to be tested (in review)
        ready_status = "In Review"
    else:
        raise ValueError(f"Unsupported phase: {phase}. Valid: review, test")

    # Query stories with ready status
    result = run_backlog_cmd(script_path, backlog_path,
        ["list", "--status", ready_status, "--fields", "id,title,feature_area,status", "--format", "json"])

    stories = result if isinstance(result, list) else result.get("stories", [])

    # Group by feature area
    by_feature = {}
    ready_stories = []

    for story in stories:
        story_id = story.get("id", "")
        title = story.get("title", "")
        feature = story.get("feature_area", "unclassified")

        ready_stories.append({
            "id": story_id,
            "title": title,
            "feature_area": feature,
        })

        if feature not in by_feature:
            by_feature[feature] = []
        by_feature[feature].append(story_id)

    return {
        "phase": phase,
        "ready_stories": ready_stories,
        "ready_count": len(ready_stories),
        "by_feature": by_feature,
    }


def handle_pipeline(args: list[str]) -> dict:
    """Main entry point for pipeline command."""
    if not args:
        raise ValueError("Subcommand required: group, agents, status, ready-for")

    subcmd = args[0]

    if subcmd == "group":
        parser = argparse.ArgumentParser(prog="agency_cli pipeline group")
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--status", default="Validated", help="Story status to group (default: Validated)")
        opts = parser.parse_args(args[1:])
        return pipeline_group(opts.backlog_path, opts.script_path, opts.status)

    elif subcmd == "agents":
        parser = argparse.ArgumentParser(prog="agency_cli pipeline agents")
        parser.add_argument("--phase", required=True)
        parser.add_argument("--feature", required=True)
        parser.add_argument("--project-root", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--objective", required=True)
        opts = parser.parse_args(args[1:])
        return pipeline_agents(opts.phase, opts.feature, opts.project_root,
                             opts.script_path, opts.backlog_path, opts.objective)

    elif subcmd == "status":
        parser = argparse.ArgumentParser(prog="agency_cli pipeline status")
        parser.add_argument("--state-path", required=True)
        opts = parser.parse_args(args[1:])
        return pipeline_status(opts.state_path)

    elif subcmd == "ready-for":
        parser = argparse.ArgumentParser(prog="agency_cli pipeline ready-for")
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--phase", required=True, choices=["review", "test"])
        opts = parser.parse_args(args[1:])
        return pipeline_ready_for(opts.backlog_path, opts.script_path, opts.phase)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: group, agents, status, ready-for")
