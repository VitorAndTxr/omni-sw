"""
agency_cli report — Markdown report generation from structured data.

Usage:
    agency_cli report context-analysis --input <analysis-json> --output <path>
    agency_cli report context-migration --input <migration-json> --output <path>
    agency_cli report phase-summary --phase <phase> --artifacts <json> --gate <json>
    agency_cli report final-summary --project-root <path> --objective <text> --phases-json <path>
"""

import argparse
import json
import os
from datetime import datetime


def generate_context_analysis_report(analysis: dict, output_path: str) -> dict:
    """Generate CONTEXT_ANALYSIS.md from token analysis data."""
    lines = [
        "# Context Token Analysis\n",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**Target:** `{analysis.get('root', 'unknown')}`\n",
        f"**Type:** {analysis.get('type', 'unknown')}\n",
        "## Summary\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total tokens | {analysis.get('total_tokens', 0):,} |",
        f"| Startup/trigger tokens | {analysis.get('startup_tokens', 0):,} |",
        f"| On-demand tokens | {analysis.get('on_demand_tokens', 0):,} |",
        f"| File count | {analysis.get('file_count', 0)} |",
        "",
    ]

    # Fragmentation candidates
    candidates = analysis.get("fragmentation_candidates", [])
    if candidates:
        lines.append("## Fragmentation Candidates\n")
        lines.append("| File | Tokens | Severity |")
        lines.append("|------|--------|----------|")
        for c in candidates:
            lines.append(f"| `{c['file']}` | {c['tokens']:,} | {c['severity']} |")
        lines.append("")

    # File breakdown
    files = analysis.get("files", {})
    if files:
        lines.append("## File Breakdown\n")
        lines.append("| File | Tokens | Load Type |")
        lines.append("|------|--------|-----------|")
        for rel_path, info in sorted(files.items(), key=lambda x: x[1].get("tokens", 0), reverse=True):
            lines.append(f"| `{rel_path}` | {info.get('tokens', 0):,} | {info.get('load_type', '?')} |")
        lines.append("")

    # Top 3 recommendations
    lines.append("## Top Recommendations\n")
    rec_num = 1
    for c in candidates[:3]:
        if c["severity"] == "mandatory":
            lines.append(f"{rec_num}. **MANDATORY** — Fragment `{c['file']}` ({c['tokens']:,} tokens). Extract sections >300 tokens to separate files.")
        elif c["severity"] == "recommended":
            lines.append(f"{rec_num}. **RECOMMENDED** — Fragment `{c['file']}` ({c['tokens']:,} tokens). Consider extracting large sections.")
        else:
            lines.append(f"{rec_num}. **CANDIDATE** — Review `{c['file']}` ({c['tokens']:,} tokens) for potential extraction.")
        rec_num += 1

    if not candidates:
        lines.append("No fragmentation candidates found. Token budget is well-optimized.\n")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return {"output": output_path, "size_chars": len(content)}


def generate_phase_summary(phase: str, artifacts: list, gate: dict | None = None) -> str:
    """Generate a phase summary line for orchestrator progress reporting."""
    phase_num = {"plan": 1, "design": 2, "validate": 3, "implement": 4, "review": 5, "test": 6, "document": 7}
    num = phase_num.get(phase.lower(), "?")

    artifacts_str = ", ".join(artifacts) if artifacts else "none"
    line = f"--- Phase {num}: {phase.title()} --- Status: COMPLETE | Artifacts: {artifacts_str}"

    if gate:
        verdict = gate.get("verdict", gate.get("combined", "?"))
        action = gate.get("action", "proceed")
        line += f" | Gate result: {verdict} | Action: {action}"

    next_phase_map = {"plan": "Design", "design": "Validate", "validate": "Implement",
                      "implement": "Review", "review": "Test", "test": "Document", "document": "DONE"}
    next_p = next_phase_map.get(phase.lower(), "?")

    if gate and gate.get("action") == "loop_back":
        target = gate.get("next_phase", "?").title()
        line += f" | Next: {target} (loop)"
    else:
        line += f" | Next: Phase {num + 1 if num != 7 else '—'}: {next_p}"

    return line


def generate_final_summary(project_root: str, objective: str, phases_data: list) -> str:
    """Generate final SDLC summary."""
    lines = [
        "# SDLC Cycle Complete\n",
        f"**Objective:** {objective}\n",
        f"**Project root:** `{project_root}`\n",
        f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "## Phase Summary\n",
    ]

    for phase in phases_data:
        name = phase.get("name", "?")
        status = phase.get("status", "?")
        artifacts = phase.get("artifacts", [])
        gate_iterations = phase.get("gate_iterations", 0)

        line = f"- **{name.title()}**: {status}"
        if artifacts:
            line += f" — Artifacts: {', '.join(artifacts)}"
        if gate_iterations > 0:
            line += f" — Gate iterations: {gate_iterations}"
        lines.append(line)

    lines.append("")
    return "\n".join(lines)


def handle_report(args: list[str]) -> dict | str:
    if not args:
        raise ValueError("Subcommand required: context-analysis, context-migration, phase-summary, final-summary")

    subcmd = args[0]

    if subcmd == "context-analysis":
        parser = argparse.ArgumentParser(prog="agency_cli report context-analysis")
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        opts = parser.parse_args(args[1:])
        with open(opts.input, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        return generate_context_analysis_report(analysis, opts.output)

    elif subcmd == "phase-summary":
        parser = argparse.ArgumentParser(prog="agency_cli report phase-summary")
        parser.add_argument("--phase", required=True)
        parser.add_argument("--artifacts", default="[]")
        parser.add_argument("--gate", default=None)
        opts = parser.parse_args(args[1:])
        artifacts = json.loads(opts.artifacts)
        gate = json.loads(opts.gate) if opts.gate else None
        return generate_phase_summary(opts.phase, artifacts, gate)

    elif subcmd == "final-summary":
        parser = argparse.ArgumentParser(prog="agency_cli report final-summary")
        parser.add_argument("--project-root", required=True)
        parser.add_argument("--objective", required=True)
        parser.add_argument("--phases-json", required=True)
        opts = parser.parse_args(args[1:])
        with open(opts.phases_json, 'r', encoding='utf-8') as f:
            phases = json.load(f)
        return generate_final_summary(opts.project_root, opts.objective, phases)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}")
