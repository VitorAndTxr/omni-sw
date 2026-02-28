"""
agency_cli phase -- Phase state machine for SDLC orchestration.

Usage:
    agency_cli phase sequence                     # Returns ordered phase list
    agency_cli phase next --current <phase> --verdict <verdict>   # Next phase after gate
    agency_cli phase artifacts --phase <phase> --project-root <path>  # Artifact paths
    agency_cli phase info --phase <phase>         # Phase metadata
    agency_cli phase prepare --phase <phase> --project-root <path> --state-path <path> --script-path <path> --backlog-path <path> --objective <text> [--skip-assists]
        # Combined: updates state + returns agent order + prompts in ONE call (reduces orchestrator turns)
"""

import argparse
import os
import json
import sys

# Canonical phase sequence
PHASES = ["plan", "design", "validate", "implement", "review", "test", "document"]

# Phase metadata
PHASE_INFO = {
    "plan": {
        "index": 0,
        "goal": "docs/PROJECT_BRIEF.md + backlog",
        "has_gate": False,
        "artifacts": ["docs/PROJECT_BRIEF.md"],
    },
    "design": {
        "index": 1,
        "goal": "docs/ARCHITECTURE.md",
        "has_gate": False,
        "artifacts": ["docs/ARCHITECTURE.md"],
    },
    "validate": {
        "index": 2,
        "goal": "docs/VALIDATION.md with dual verdicts",
        "has_gate": True,
        "gate_type": "dual",
        "artifacts": ["docs/VALIDATION.md"],
    },
    "implement": {
        "index": 3,
        "goal": "Source code in src/",
        "has_gate": False,
        "artifacts": ["src/"],
    },
    "review": {
        "index": 4,
        "goal": "docs/REVIEW.md",
        "has_gate": True,
        "gate_type": "single",
        "artifacts": ["docs/REVIEW.md"],
    },
    "test": {
        "index": 5,
        "goal": "Tests in tests/ + docs/TEST_REPORT.md",
        "has_gate": True,
        "gate_type": "single_extended",
        "artifacts": ["tests/", "docs/TEST_REPORT.md"],
    },
    "document": {
        "index": 6,
        "goal": "README.md, CHANGELOG.md, docs/API_REFERENCE.md",
        "has_gate": False,
        "artifacts": ["README.md", "CHANGELOG.md", "docs/API_REFERENCE.md"],
    },
}


def get_next_phase(current: str, verdict: str) -> dict:
    """Determine next phase based on current phase and gate verdict."""
    current = current.lower()
    verdict = verdict.upper().strip()

    if current == "validate":
        # Dual gate: expects "APPROVED,APPROVED" or "REPROVED,APPROVED" etc.
        parts = [v.strip() for v in verdict.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Validate gate requires two verdicts (PM,TL). Got: {verdict}")
        pm_verdict, tl_verdict = parts

        if pm_verdict == "APPROVED" and tl_verdict == "APPROVED":
            return {"next_phase": "implement", "action": "proceed", "reason": "Both approved"}
        elif pm_verdict == "REPROVED":
            return {"next_phase": "plan", "action": "loop_back", "reason": "PM reproved -- return to Plan"}
        elif tl_verdict == "REPROVED":
            return {"next_phase": "design", "action": "loop_back", "reason": "TL reproved -- return to Design"}

    elif current == "review":
        if verdict == "PASS":
            return {"next_phase": "test", "action": "proceed", "reason": "Review passed"}
        elif verdict == "FAIL":
            return {"next_phase": "implement", "action": "loop_back", "reason": "Blocking issues found"}

    elif current == "test":
        if verdict == "PASS":
            return {"next_phase": "document", "action": "proceed", "reason": "All tests pass"}
        elif verdict == "FAIL_BUG":
            return {"next_phase": "implement", "action": "loop_back", "reason": "Bug found -- return to Implement"}
        elif verdict == "FAIL_TEST":
            return {
                "next_phase": "test",
                "action": "fix_tests",
                "reason": "Test issue -- spawn qa-test-fix to fix tests, then re-run",
                "spawn_fix_agent": True,
            }

    raise ValueError(f"Invalid phase/verdict combination: {current}/{verdict}")


def get_artifacts(phase: str, project_root: str) -> dict:
    """Resolve artifact absolute paths for a phase."""
    phase = phase.lower()
    if phase not in PHASE_INFO:
        raise ValueError(f"Unknown phase: {phase}. Valid: {', '.join(PHASES)}")

    info = PHASE_INFO[phase]
    resolved = []
    for artifact in info["artifacts"]:
        resolved.append({
            "relative": artifact,
            "absolute": os.path.join(project_root, artifact),
            "exists": os.path.exists(os.path.join(project_root, artifact)),
        })

    return {"phase": phase, "artifacts": resolved}


def validate_artifacts(phase: str, project_root: str) -> dict:
    """Check if required artifacts from a phase exist before proceeding."""
    phase = phase.lower()
    if phase not in PHASE_INFO:
        raise ValueError(f"Unknown phase: {phase}. Valid: {', '.join(PHASES)}")

    info = PHASE_INFO[phase]
    results = []
    all_exist = True

    for artifact in info["artifacts"]:
        abs_path = os.path.join(project_root, artifact)
        exists = os.path.exists(abs_path)
        is_dir = os.path.isdir(abs_path)
        is_empty = False

        if exists:
            if is_dir:
                # Check directory is not empty
                is_empty = len(os.listdir(abs_path)) == 0
            else:
                is_empty = os.path.getsize(abs_path) == 0

        valid = exists and not is_empty
        if not valid:
            all_exist = False

        results.append({
            "artifact": artifact,
            "absolute": abs_path,
            "exists": exists,
            "is_empty": is_empty,
            "valid": valid,
        })

    # Determine which phase this blocks
    idx = PHASES.index(phase)
    next_phase = PHASES[idx + 1] if idx < len(PHASES) - 1 else None

    return {
        "phase": phase,
        "all_valid": all_exist,
        "can_proceed": all_exist,
        "next_phase": next_phase,
        "artifacts": results,
        "message": (
            f"All artifacts for {phase} are present. Ready to proceed to {next_phase}."
            if all_exist
            else f"Missing artifacts for {phase}: {', '.join(a['artifact'] for a in results if not a['valid'])}"
        ),
    }


def prepare_phase(args: list[str]) -> dict:
    """Combined operation: update state + return agent order + all prompts in ONE call.

    This replaces 3+ separate CLI calls per phase transition, reducing orchestrator turns
    and context growth in the main session.
    """
    parser = argparse.ArgumentParser(prog="agency_cli phase prepare")
    parser.add_argument("--phase", required=True, help="Phase to prepare")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    parser.add_argument("--script-path", required=True, help="Path to backlog_manager.py")
    parser.add_argument("--backlog-path", required=True, help="Path to backlog directory")
    parser.add_argument("--objective", required=False, default=None, help="Project objective")
    parser.add_argument("--objective-stdin", action="store_true",
                        help="Read objective from stdin")
    parser.add_argument("--skip-assists", action="store_true",
                        help="Exclude assist agents (only spawn leads)")
    opts = parser.parse_args(args)

    if opts.objective_stdin:
        objective = sys.stdin.read().strip()
    elif opts.objective:
        objective = opts.objective
    else:
        raise ValueError("Either --objective or --objective-stdin is required")

    phase = opts.phase.lower().strip()
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}. Valid: {', '.join(PHASES)}")

    # --- 1. Check prerequisites via state ---
    from commands.state import _load_state, _save_state, _get_now_iso, PHASES as STATE_PHASES
    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    # Check can-proceed logic inline (avoid circular import overhead)
    dependencies = {
        "plan": [], "design": ["plan"], "validate": ["design"],
        "implement": ["validate"], "review": ["implement"],
        "test": ["review"], "document": ["test"],
    }
    for required in dependencies.get(phase, []):
        req_status = state["phases"][required]["status"]
        if req_status != "completed":
            return {
                "ready": False,
                "blocked_by": required,
                "reason": f"Phase {required} has status: {req_status}",
            }

    # --- 2. Mark phase in_progress ---
    phase_obj = state["phases"][phase]
    old_status = phase_obj["status"]
    now = _get_now_iso()
    if old_status != "in_progress":
        phase_obj["status"] = "in_progress"
        phase_obj["started_at"] = now
        state["current_phase"] = phase
    _save_state(state_path, state)

    # --- 3. Get agent order + prompts ---
    from commands.agent import (
        AGENT_MATRIX, PHASE_ORDER, GATE_SUFFIXES,
        get_agent_name, generate_prompt, validate_phase as agent_validate_phase
    )

    waves = []
    for i, wave_roles in enumerate(PHASE_ORDER.get(phase, [])):
        wave_agents = []
        for role in wave_roles:
            key = (phase, role)
            if key not in AGENT_MATRIX:
                continue
            info = AGENT_MATRIX[key]

            # Skip assists if --skip-assists
            if opts.skip_assists and info["type"] == "assist":
                continue

            agent_name = get_agent_name(role, phase, info["type"])
            prompt = generate_prompt(
                role, phase, opts.project_root,
                opts.script_path, opts.backlog_path, objective, info["type"]
            )

            wave_agents.append({
                "role": role,
                "name": agent_name,
                "model": info["model"],
                "type": info["type"],
                "prompt": prompt,
                "skill_command": info["skill"],
            })

        if wave_agents:
            waves.append({
                "wave": i + 1,
                "parallel": len(wave_agents) > 1,
                "agents": wave_agents,
            })

    # --- 4. Get phase artifacts ---
    info = PHASE_INFO[phase]
    artifacts = []
    for artifact in info["artifacts"]:
        abs_path = os.path.join(opts.project_root, artifact)
        artifacts.append({
            "relative": artifact,
            "absolute": abs_path,
            "exists": os.path.exists(abs_path),
        })

    return {
        "ready": True,
        "phase": phase,
        "goal": info["goal"],
        "has_gate": info.get("has_gate", False),
        "state_updated": True,
        "skip_assists": opts.skip_assists,
        "waves": waves,
        "total_agents": sum(len(w["agents"]) for w in waves),
        "artifacts": artifacts,
    }


def handle_phase(args: list[str]) -> dict | list:
    if not args:
        raise ValueError("Subcommand required: sequence, next, artifacts, info, validate-artifacts, prepare")

    subcmd = args[0]

    if subcmd == "sequence":
        return {"phases": PHASES, "total": len(PHASES)}

    elif subcmd == "next":
        parser = argparse.ArgumentParser(prog="agency_cli phase next")
        parser.add_argument("--current", required=True, help="Current phase name")
        parser.add_argument("--verdict", required=True, help="Gate verdict(s)")
        opts = parser.parse_args(args[1:])
        return get_next_phase(opts.current, opts.verdict)

    elif subcmd == "artifacts":
        parser = argparse.ArgumentParser(prog="agency_cli phase artifacts")
        parser.add_argument("--phase", required=True, help="Phase name")
        parser.add_argument("--project-root", required=True, help="Project root path")
        opts = parser.parse_args(args[1:])
        return get_artifacts(opts.phase, opts.project_root)

    elif subcmd == "info":
        parser = argparse.ArgumentParser(prog="agency_cli phase info")
        parser.add_argument("--phase", required=True, help="Phase name")
        opts = parser.parse_args(args[1:])
        phase = opts.phase.lower()
        if phase not in PHASE_INFO:
            raise ValueError(f"Unknown phase: {phase}")
        return {"phase": phase, **PHASE_INFO[phase]}

    elif subcmd == "validate-artifacts":
        parser = argparse.ArgumentParser(prog="agency_cli phase validate-artifacts")
        parser.add_argument("--phase", required=True, help="Phase to validate")
        parser.add_argument("--project-root", required=True, help="Project root path")
        opts = parser.parse_args(args[1:])
        return validate_artifacts(opts.phase, opts.project_root)

    elif subcmd == "prepare":
        return prepare_phase(args[1:])

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: sequence, next, artifacts, info, validate-artifacts, prepare")
