"""
agency_cli state -- Persistent state machine for SDLC agency workflow.

Manages STATE.json file tracking phases, gate verdicts, iterations, timestamps, and pipeline status.

Usage:
    agency_cli state init --project <name> --objective <text> --state-path <path>
    agency_cli state update --state-path <path> --phase <phase> --status <status> [--agent <name> --agent-status <status>] [--notes <text>]
    agency_cli state gate-record --state-path <path> --phase <phase> --verdict <verdict> [--pm <APPROVED|REPROVED>] [--tl <APPROVED|REPROVED>] [--tests-passed <n>] [--tests-failed <n>]
    agency_cli state query --state-path <path> [--phase <phase>] [--field <field>]
    agency_cli state can-proceed --state-path <path> --to-phase <phase>
    agency_cli state summary --state-path <path>
"""

import argparse
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone

# Canonical phase sequence
PHASES = ["plan", "design", "validate", "implement", "review", "test", "document"]
GATE_PHASES = ["validate", "review", "test"]


def _get_now_iso():
    """Get current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(filepath: str, data: dict) -> None:
    """Write JSON to file atomically using temp file + rename."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Write to temp file in same directory as target
    temp_fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(filepath),
        prefix=".tmp_",
        suffix=".json"
    )
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Atomic rename
        shutil.move(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _load_state(state_path: str) -> dict:
    """Load STATE.json file."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")

    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_state(state_path: str, state: dict) -> None:
    """Save STATE.json file atomically."""
    state["updated_at"] = _get_now_iso()
    _atomic_write_json(state_path, state)


def _validate_phase(phase: str) -> str:
    """Validate and normalize phase name."""
    phase = phase.lower().strip()
    if phase not in PHASES:
        raise ValueError(f"Invalid phase: {phase}. Valid: {', '.join(PHASES)}")
    return phase


def _validate_status(status: str) -> str:
    """Validate and normalize status."""
    status = status.lower().strip()
    if status not in ("pending", "in_progress", "completed", "skipped"):
        raise ValueError(f"Invalid status: {status}")
    return status


def _validate_verdict(verdict: str) -> str:
    """Validate and normalize verdict."""
    verdict = verdict.upper().strip()
    if verdict not in ("APPROVED", "REPROVED", "PASS", "FAIL", "FAIL_BUG", "FAIL_TEST"):
        raise ValueError(f"Invalid verdict: {verdict}")
    return verdict


def create_initial_state(project_name: str, objective: str) -> dict:
    """Create a new STATE.json structure."""
    now = _get_now_iso()

    phases = {}
    for phase in PHASES:
        phases[phase] = {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "artifacts": [],
            "agents": {},
            "notes": "",
        }

    return {
        "version": "1.0",
        "project": project_name,
        "objective": objective,
        "created_at": now,
        "updated_at": now,
        "current_phase": None,
        "status": "in_progress",
        "phases": phases,
        "metrics": {
            "total_phases": len(PHASES),
            "completed_phases": 0,
            "total_gate_iterations": 0,
            "phase_durations": {},
        },
    }


def init_state(args: list[str]) -> dict:
    """Handle 'state init' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state init")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--objective", required=True, help="Project objective")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json file")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    if os.path.exists(state_path):
        raise FileExistsError(f"State file already exists: {state_path}")

    state = create_initial_state(opts.project, opts.objective)
    _save_state(state_path, state)

    return {
        "status": "created",
        "state_path": state_path,
        "project": opts.project,
        "objective": opts.objective,
        "initial_state": state,
    }


def update_phase_status(args: list[str]) -> dict:
    """Handle 'state update' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state update")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    parser.add_argument("--phase", required=True, help="Phase name")
    parser.add_argument("--status", required=True, help="Status: pending|in_progress|completed|skipped")
    parser.add_argument("--agent", help="Agent name")
    parser.add_argument("--agent-status", help="Agent status")
    parser.add_argument("--notes", default="", help="Notes for phase")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    phase = _validate_phase(opts.phase)
    new_status = _validate_status(opts.status)

    phase_obj = state["phases"][phase]
    old_status = phase_obj["status"]

    # Update status
    phase_obj["status"] = new_status

    # Handle timestamp transitions
    now = _get_now_iso()
    if old_status != "in_progress" and new_status == "in_progress":
        phase_obj["started_at"] = now
        state["current_phase"] = phase

    if new_status == "completed" and old_status != "completed":
        phase_obj["completed_at"] = now
        if phase_obj["started_at"]:
            # Calculate duration in seconds
            start = datetime.fromisoformat(phase_obj["started_at"])
            end = datetime.fromisoformat(now)
            duration_seconds = int((end - start).total_seconds())
            state["metrics"]["phase_durations"][phase] = duration_seconds

    # Update agent status if provided
    if opts.agent:
        agent_name = opts.agent.strip()
        agent_status = opts.agent_status.strip() if opts.agent_status else "completed"
        phase_obj["agents"][agent_name] = agent_status

    # Update notes
    if opts.notes:
        phase_obj["notes"] = opts.notes

    # Recalculate completed_phases count
    completed_count = sum(
        1 for p in state["phases"].values()
        if p["status"] == "completed"
    )
    state["metrics"]["completed_phases"] = completed_count

    # Update overall status
    if completed_count == len(PHASES):
        state["status"] = "completed"
    elif any(p["status"] == "in_progress" for p in state["phases"].values()):
        state["status"] = "in_progress"

    _save_state(state_path, state)

    return {
        "status": "updated",
        "phase": phase,
        "phase_status": new_status,
        "current_phase": state["current_phase"],
        "completed_phases": state["metrics"]["completed_phases"],
        "overall_status": state["status"],
    }


def record_gate_verdict(args: list[str]) -> dict:
    """Handle 'state gate-record' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state gate-record")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    parser.add_argument("--phase", required=True, help="Gate phase: validate|review|test")
    parser.add_argument("--verdict", required=True, help="Verdict value")
    parser.add_argument("--pm", help="PM verdict (for validate phase)")
    parser.add_argument("--tl", help="TL verdict (for validate phase)")
    parser.add_argument("--tests-passed", type=int, help="Number of tests passed")
    parser.add_argument("--tests-failed", type=int, help="Number of tests failed")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    phase = _validate_phase(opts.phase)
    if phase not in GATE_PHASES:
        raise ValueError(f"Phase {phase} is not a gate phase. Gate phases: {', '.join(GATE_PHASES)}")

    phase_obj = state["phases"][phase]

    # Ensure gate object exists
    if "gate" not in phase_obj:
        phase_obj["gate"] = {
            "iterations": 0,
            "max_iterations": 3,
            "verdicts": [],
        }

    gate = phase_obj["gate"]
    gate["iterations"] += 1
    iteration_num = gate["iterations"]

    # Create verdict record
    verdict_record = {"iteration": iteration_num}

    if phase == "validate":
        # Validate gate expects PM and TL verdicts
        pm_verdict = _validate_verdict(opts.pm) if opts.pm else None
        tl_verdict = _validate_verdict(opts.tl) if opts.tl else None

        if not pm_verdict or not tl_verdict:
            raise ValueError("Validate gate requires both --pm and --tl verdicts")

        verdict_record["pm"] = pm_verdict
        verdict_record["tl"] = tl_verdict
        # Combined is APPROVED only if both are APPROVED
        verdict_record["combined"] = "APPROVED" if (pm_verdict == "APPROVED" and tl_verdict == "APPROVED") else "REPROVED"

    elif phase == "review":
        # Review gate expects single PASS/FAIL verdict
        verdict = _validate_verdict(opts.verdict)
        if verdict not in ("PASS", "FAIL"):
            raise ValueError("Review gate expects PASS or FAIL verdict")
        verdict_record["verdict"] = verdict

    elif phase == "test":
        # Test gate expects PASS, FAIL_BUG, or FAIL_TEST
        verdict = _validate_verdict(opts.verdict)
        if verdict not in ("PASS", "FAIL_BUG", "FAIL_TEST"):
            raise ValueError("Test gate expects PASS, FAIL_BUG, or FAIL_TEST verdict")
        verdict_record["verdict"] = verdict
        if opts.tests_passed is not None:
            verdict_record["tests_passed"] = opts.tests_passed
        if opts.tests_failed is not None:
            verdict_record["tests_failed"] = opts.tests_failed

    gate["verdicts"].append(verdict_record)
    state["metrics"]["total_gate_iterations"] += 1

    _save_state(state_path, state)

    return {
        "status": "recorded",
        "phase": phase,
        "iteration": iteration_num,
        "verdict_record": verdict_record,
    }


def query_state(args: list[str]) -> dict | str:
    """Handle 'state query' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state query")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    parser.add_argument("--phase", help="Phase name to query")
    parser.add_argument("--field", help="Specific field to query")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    # If field is specified, return that specific field
    if opts.field:
        field = opts.field.strip()
        if field not in state:
            raise ValueError(f"Field not found: {field}")
        return state[field]

    # If phase is specified, return that phase's state
    if opts.phase:
        phase = _validate_phase(opts.phase)
        return {"phase": phase, **state["phases"][phase]}

    # Otherwise return full state
    return state


def can_proceed_to_phase(args: list[str]) -> dict:
    """Handle 'state can-proceed' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state can-proceed")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    parser.add_argument("--to-phase", required=True, help="Target phase")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    target_phase = _validate_phase(opts.to_phase)
    target_idx = PHASES.index(target_phase)

    # Define phase dependencies
    dependencies = {
        "plan": [],
        "design": ["plan"],
        "validate": ["design"],
        "implement": ["validate"],
        "review": ["implement"],
        "test": ["review"],
        "document": ["test"],
    }

    # Check phase dependencies
    required_phases = dependencies[target_phase]
    for required in required_phases:
        req_status = state["phases"][required]["status"]
        if req_status != "completed":
            return {
                "allowed": False,
                "reason": f"Phase {required} is required but has status: {req_status}",
                "blocking_phase": required,
                "to_phase": target_phase,
            }

    # For implement, check validate gate approval
    if target_phase == "implement":
        validate_phase = state["phases"]["validate"]
        if "gate" in validate_phase:
            gate = validate_phase["gate"]
            if gate["verdicts"]:
                last_verdict = gate["verdicts"][-1]
                if last_verdict.get("combined") != "APPROVED":
                    return {
                        "allowed": False,
                        "reason": "Validate gate must have combined APPROVED verdict",
                        "blocking_phase": "validate",
                        "to_phase": target_phase,
                    }
        else:
            return {
                "allowed": False,
                "reason": "Validate gate has no verdicts recorded",
                "blocking_phase": "validate",
                "to_phase": target_phase,
            }

    # For test, check review gate passed
    if target_phase == "test":
        review_phase = state["phases"]["review"]
        if "gate" in review_phase:
            gate = review_phase["gate"]
            if gate["verdicts"]:
                last_verdict = gate["verdicts"][-1]
                if last_verdict.get("verdict") != "PASS":
                    return {
                        "allowed": False,
                        "reason": "Review gate must have PASS verdict",
                        "blocking_phase": "review",
                        "to_phase": target_phase,
                    }
        else:
            return {
                "allowed": False,
                "reason": "Review gate has no verdicts recorded",
                "blocking_phase": "review",
                "to_phase": target_phase,
            }

    # For document, check test gate passed
    if target_phase == "document":
        test_phase = state["phases"]["test"]
        if "gate" in test_phase:
            gate = test_phase["gate"]
            if gate["verdicts"]:
                last_verdict = gate["verdicts"][-1]
                if last_verdict.get("verdict") != "PASS":
                    return {
                        "allowed": False,
                        "reason": "Test gate must have PASS verdict",
                        "blocking_phase": "test",
                        "to_phase": target_phase,
                    }
        else:
            return {
                "allowed": False,
                "reason": "Test gate has no verdicts recorded",
                "blocking_phase": "test",
                "to_phase": target_phase,
            }

    return {
        "allowed": True,
        "reason": "All dependencies satisfied",
        "to_phase": target_phase,
        "blocking_phase": None,
    }


def state_summary(args: list[str]) -> dict:
    """Handle 'state summary' subcommand."""
    parser = argparse.ArgumentParser(prog="agency_cli state summary")
    parser.add_argument("--state-path", required=True, help="Path to STATE.json")
    opts = parser.parse_args(args)

    state_path = os.path.abspath(opts.state_path)
    state = _load_state(state_path)

    # Build phase summary
    phase_summary = {}
    for phase in PHASES:
        phase_obj = state["phases"][phase]
        summary = {
            "status": phase_obj["status"],
            "duration_seconds": state["metrics"]["phase_durations"].get(phase),
        }

        if phase_obj["agents"]:
            summary["agents"] = phase_obj["agents"]

        if "gate" in phase_obj and phase_obj["gate"]["verdicts"]:
            gate = phase_obj["gate"]
            summary["gate"] = {
                "iterations": gate["iterations"],
                "max_iterations": gate["max_iterations"],
                "last_verdict": gate["verdicts"][-1],
            }

        if phase_obj["notes"]:
            summary["notes"] = phase_obj["notes"]

        phase_summary[phase] = summary

    return {
        "project": state["project"],
        "objective": state["objective"],
        "current_phase": state["current_phase"],
        "overall_status": state["status"],
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "metrics": state["metrics"],
        "phases": phase_summary,
    }


def handle_state(args: list[str]) -> dict | str:
    """Main handler for state subcommands."""
    if not args:
        raise ValueError("Subcommand required: init, update, gate-record, query, can-proceed, summary")

    subcmd = args[0]

    if subcmd == "init":
        return init_state(args[1:])
    elif subcmd == "update":
        return update_phase_status(args[1:])
    elif subcmd == "gate-record":
        return record_gate_verdict(args[1:])
    elif subcmd == "query":
        return query_state(args[1:])
    elif subcmd == "can-proceed":
        return can_proceed_to_phase(args[1:])
    elif subcmd == "summary":
        return state_summary(args[1:])
    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: init, update, gate-record, query, can-proceed, summary")
