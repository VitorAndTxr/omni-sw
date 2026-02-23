"""
agency_cli agent -- Agent configuration: model lookup, naming, prompt generation, ordering.

Usage:
    agency_cli agent model --role <role> --phase <phase>
    agency_cli agent name --role <role> --phase <phase> --type <lead|assist>
    agency_cli agent list --phase <phase>
    agency_cli agent prompt --role <role> --phase <phase> --project-root <path> ...
    agency_cli agent order --phase <phase>
"""

import argparse
import json
import os

VALID_ROLES = {"pm", "po", "tl", "dev", "qa"}
VALID_PHASES = {"plan", "design", "validate", "implement", "review", "test", "document"}


def validate_role(role: str) -> str:
    """Validate and normalize role name."""
    role = role.strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: '{role}'. Valid roles: {', '.join(sorted(VALID_ROLES))}")
    return role


def validate_phase(phase: str) -> str:
    """Validate and normalize phase name."""
    phase = phase.strip().lower()
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: '{phase}'. Valid phases: {', '.join(VALID_PHASES)}")
    return phase


# Full agent matrix: (phase, role) -> {model, type, description}
AGENT_MATRIX = {
    # Plan
    ("plan", "pm"):  {"model": "opus",   "type": "lead",   "desc": "Lead: produce PROJECT_BRIEF.md",        "skill": "/pm plan"},
    ("plan", "po"):  {"model": "sonnet", "type": "lead",   "desc": "Lead: create backlog from brief",       "skill": "/po plan"},
    ("plan", "tl"):  {"model": "haiku",  "type": "assist", "desc": "Assist: risk notes",                    "skill": "/tl plan"},
    ("plan", "dev"): {"model": "haiku",  "type": "assist", "desc": "Assist: implementability notes",        "skill": "/dev plan"},
    ("plan", "qa"):  {"model": "haiku",  "type": "assist", "desc": "Assist: testability notes",             "skill": "/qa plan"},
    # Design
    ("design", "tl"):  {"model": "opus",   "type": "lead",   "desc": "Lead: produce ARCHITECTURE.md",      "skill": "/tl design"},
    ("design", "dev"): {"model": "haiku",  "type": "assist", "desc": "Assist: implementability review",     "skill": "/dev design"},
    ("design", "qa"):  {"model": "haiku",  "type": "assist", "desc": "Assist: testability review",          "skill": "/qa design"},
    # Validate
    ("validate", "pm"): {"model": "opus",  "type": "lead",   "desc": "Lead: business validation",           "skill": "/pm validate"},
    ("validate", "tl"): {"model": "opus",  "type": "lead",   "desc": "Lead: technical validation",          "skill": "/tl validate"},
    ("validate", "po"): {"model": "haiku", "type": "assist", "desc": "Assist: backlog alignment check",     "skill": "/po validate"},
    # Implement
    ("implement", "dev"): {"model": "sonnet", "type": "lead",   "desc": "Lead: write production code",      "skill": "/dev implement"},
    ("implement", "tl"):  {"model": "sonnet", "type": "assist", "desc": "Assist: on-demand tech guidance",  "skill": "/tl implement"},
    # Review
    ("review", "tl"): {"model": "sonnet", "type": "lead",   "desc": "Lead: code review, produce REVIEW.md", "skill": "/tl review"},
    ("review", "qa"): {"model": "haiku",  "type": "assist", "desc": "Assist: correctness review",            "skill": "/qa review"},
    # Test
    ("test", "qa"): {"model": "sonnet", "type": "lead",   "desc": "Lead: write/run tests, TEST_REPORT.md",  "skill": "/qa test"},
    ("test", "tl"): {"model": "haiku",  "type": "assist", "desc": "Assist: coverage review",                 "skill": "/tl test"},
    # Document
    ("document", "pm"):  {"model": "sonnet", "type": "lead",   "desc": "Lead: README.md, CHANGELOG.md",          "skill": "/pm document"},
    ("document", "tl"):  {"model": "sonnet", "type": "lead",   "desc": "Lead: API_REFERENCE.md, ARCHITECTURE.md", "skill": "/tl document"},
    ("document", "po"):  {"model": "haiku",  "type": "assist", "desc": "Assist: documentation verification",      "skill": "/po document"},
    ("document", "dev"): {"model": "haiku",  "type": "assist", "desc": "Assist: developer documentation",         "skill": "/dev document"},
    ("document", "qa"):  {"model": "haiku",  "type": "assist", "desc": "Assist: test documentation",              "skill": "/qa document"},
}

# Sequential dependencies within phases
PHASE_ORDER = {
    "plan":     [["pm"], ["tl", "dev", "qa"], ["po"]],  # PM first, TL/Dev/QA parallel, PO after PM
    "design":   [["tl"], ["dev", "qa"]],                 # TL first, Dev/QA after
    "validate": [["pm", "tl"], ["po"]],                  # PM+TL parallel, PO after/parallel
    "implement":[["dev", "tl"]],                         # Dev leads, TL on-demand (both together)
    "review":   [["tl"], ["qa"]],                        # TL first, QA after
    "test":     [["qa"], ["tl"]],                        # QA first, TL after
    "document": [["pm", "tl"], ["po", "dev", "qa"]],    # PM+TL parallel, rest after
}

# Gate verdict suffixes for lead prompts
GATE_SUFFIXES = {
    "validate": 'End output with [VERDICT:APPROVED] or [VERDICT:REPROVED].',
    "review":   'End output with [GATE:PASS] or [GATE:FAIL].',
    "test":     'End output with [GATE:PASS], [GATE:FAIL_BUG], or [GATE:FAIL_TEST].',
}


def get_agent_name(role: str, phase: str, agent_type: str) -> str:
    """Generate deterministic agent name."""
    role = validate_role(role)
    phase = validate_phase(phase)
    if agent_type == "assist":
        return f"{role}-{phase}-assist"
    return f"{role}-{phase}"


def get_model(role: str, phase: str) -> str:
    """Lookup model for role/phase from matrix."""
    role = validate_role(role)
    phase = validate_phase(phase)
    key = (phase, role)
    if key not in AGENT_MATRIX:
        raise ValueError(f"No agent defined for role={role}, phase={phase}")
    return AGENT_MATRIX[key]["model"]


def list_agents(phase: str) -> list[dict]:
    """List all agents for a phase with full config."""
    phase = validate_phase(phase)
    agents = []
    for (p, role), info in AGENT_MATRIX.items():
        if p == phase:
            agents.append({
                "role": role,
                "name": get_agent_name(role, phase, info["type"]),
                "model": info["model"],
                "type": info["type"],
                "description": info["desc"],
                "skill_command": info["skill"],
            })
    if not agents:
        raise ValueError(f"No agents defined for phase: {phase}")
    return agents


def generate_prompt(role: str, phase: str, project_root: str, script_path: str,
                    backlog_path: str, objective: str, agent_type: str = None) -> str:
    """Generate the full agent spawn prompt."""
    role = validate_role(role)
    phase = validate_phase(phase)
    key = (phase, role)
    if key not in AGENT_MATRIX:
        raise ValueError(f"No agent defined for role={role}, phase={phase}")

    info = AGENT_MATRIX[key]
    atype = agent_type or info["type"]
    skill_cmd = info["skill"]

    if atype == "lead":
        prompt = (
            f"You are the {role.upper()}. Invoke the `{skill_cmd}` skill. "
            f"The project objective is: {objective}. "
            f"The project root is: {project_root}. "
            f"The backlog script is at: {script_path}. "
            f"The backlog path is: {backlog_path}. "
            f"Read CLAUDE.md for context. "
            f"If you need clarification, list all questions prefixed with [QUESTIONS]. "
            f"Do NOT use AskUserQuestion -- return questions to me. "
            f"When done, mark your task as completed via TaskUpdate."
        )
        # Add gate suffix if applicable
        gate_suffix = GATE_SUFFIXES.get(phase.lower())
        if gate_suffix:
            prompt += f" {gate_suffix}"
    else:
        prompt = (
            f"You are the {role.upper()} assist. Invoke the `{skill_cmd}` skill. "
            f"The project objective is: {objective}. "
            f"The project root is: {project_root}. "
            f"The backlog script is at: {script_path}. "
            f"The backlog path is: {backlog_path}. "
            f"Read CLAUDE.md for context. "
            f"Provide your [NOTES] and review findings. "
            f"Do NOT use AskUserQuestion -- return questions to me. "
            f"When done, mark your task as completed via TaskUpdate."
        )

    return prompt


def get_order(phase: str) -> list[dict]:
    """Get execution order (waves) for a phase."""
    phase = validate_phase(phase)
    if phase not in PHASE_ORDER:
        raise ValueError(f"Unknown phase: {phase}")

    waves = []
    for i, wave_roles in enumerate(PHASE_ORDER[phase]):
        wave_agents = []
        for role in wave_roles:
            key = (phase, role)
            if key in AGENT_MATRIX:
                info = AGENT_MATRIX[key]
                wave_agents.append({
                    "role": role,
                    "name": get_agent_name(role, phase, info["type"]),
                    "model": info["model"],
                    "type": info["type"],
                })
        waves.append({
            "wave": i + 1,
            "parallel": len(wave_agents) > 1,
            "agents": wave_agents,
            "blocked_by": f"wave_{i}" if i > 0 else None,
        })

    return waves


def handle_agent(args: list[str]) -> dict | list | str:
    if not args:
        raise ValueError("Subcommand required: model, name, list, prompt, order")

    subcmd = args[0]

    if subcmd == "model":
        parser = argparse.ArgumentParser(prog="agency_cli agent model")
        parser.add_argument("--role", required=True)
        parser.add_argument("--phase", required=True)
        opts = parser.parse_args(args[1:])
        return {"model": get_model(opts.role, opts.phase)}

    elif subcmd == "name":
        parser = argparse.ArgumentParser(prog="agency_cli agent name")
        parser.add_argument("--role", required=True)
        parser.add_argument("--phase", required=True)
        parser.add_argument("--type", required=True, choices=["lead", "assist"])
        opts = parser.parse_args(args[1:])
        return {"name": get_agent_name(opts.role, opts.phase, opts.type)}

    elif subcmd == "list":
        parser = argparse.ArgumentParser(prog="agency_cli agent list")
        parser.add_argument("--phase", required=True)
        opts = parser.parse_args(args[1:])
        return list_agents(opts.phase)

    elif subcmd == "prompt":
        parser = argparse.ArgumentParser(prog="agency_cli agent prompt")
        parser.add_argument("--role", required=True)
        parser.add_argument("--phase", required=True)
        parser.add_argument("--project-root", required=True)
        parser.add_argument("--script-path", required=True)
        parser.add_argument("--backlog-path", required=True)
        parser.add_argument("--objective", required=False, default=None)
        parser.add_argument("--objective-stdin", action="store_true",
                            help="Read objective from stdin (avoids shell escaping issues)")
        parser.add_argument("--type", choices=["lead", "assist"], default=None)
        opts = parser.parse_args(args[1:])
        if opts.objective_stdin:
            import sys as _sys
            objective = _sys.stdin.read().strip()
        elif opts.objective:
            objective = opts.objective
        else:
            raise ValueError("Either --objective or --objective-stdin is required")
        prompt = generate_prompt(
            opts.role, opts.phase, opts.project_root,
            opts.script_path, opts.backlog_path, objective, opts.type
        )
        return {"prompt": prompt, "model": get_model(opts.role, opts.phase),
                "name": get_agent_name(opts.role, opts.phase,
                    opts.type or AGENT_MATRIX[(opts.phase.lower(), opts.role.lower())]["type"])}

    elif subcmd == "order":
        parser = argparse.ArgumentParser(prog="agency_cli agent order")
        parser.add_argument("--phase", required=True)
        opts = parser.parse_args(args[1:])
        return get_order(opts.phase)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}")
