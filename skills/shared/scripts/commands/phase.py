"""
agency_cli phase — Phase state machine for SDLC orchestration.

Usage:
    agency_cli phase sequence                     # Returns ordered phase list
    agency_cli phase next --current <phase> --verdict <verdict>   # Next phase after gate
    agency_cli phase artifacts --phase <phase> --project-root <path>  # Artifact paths
    agency_cli phase info --phase <phase>         # Phase metadata
"""

import argparse
import os
import json

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
            return {"next_phase": "plan", "action": "loop_back", "reason": "PM reproved — return to Plan"}
        elif tl_verdict == "REPROVED":
            return {"next_phase": "design", "action": "loop_back", "reason": "TL reproved — return to Design"}

    elif current == "review":
        if verdict == "PASS":
            return {"next_phase": "test", "action": "proceed", "reason": "Review passed"}
        elif verdict == "FAIL":
            return {"next_phase": "implement", "action": "loop_back", "reason": "Blocking issues found"}

    elif current == "test":
        if verdict == "PASS":
            return {"next_phase": "document", "action": "proceed", "reason": "All tests pass"}
        elif verdict == "FAIL_BUG":
            return {"next_phase": "implement", "action": "loop_back", "reason": "Bug found — return to Implement"}
        elif verdict == "FAIL_TEST":
            return {
                "next_phase": "test",
                "action": "fix_tests",
                "reason": "Test issue — spawn qa-test-fix to fix tests, then re-run",
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


def handle_phase(args: list[str]) -> dict | list:
    if not args:
        raise ValueError("Subcommand required: sequence, next, artifacts, info")

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

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: sequence, next, artifacts, info")
