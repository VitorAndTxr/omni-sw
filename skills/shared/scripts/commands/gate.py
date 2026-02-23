"""
agency_cli gate -- Parse gate verdicts from agent output.

Usage:
    agency_cli gate parse --file <path> --phase <validate|review|test>
    agency_cli gate parse --text <text> --phase <validate|review|test>
    agency_cli gate check --phase <phase> --iteration <n> --max <n>
"""

import argparse
import re
import json
import sys


def _resolve_text_input(opts) -> str:
    """Resolve text from --file, --text, or --text-stdin."""
    if getattr(opts, 'text_stdin', False):
        return sys.stdin.read().strip()
    elif opts.file:
        with open(opts.file, 'r', encoding='utf-8') as f:
            return f.read()
    elif opts.text:
        return opts.text
    else:
        raise ValueError("Either --file, --text, or --text-stdin is required")


def parse_verdict_from_text(text: str, phase: str) -> dict:
    """Extract verdict markers from text based on phase type."""
    phase = phase.lower()

    if phase == "validate":
        # Look for [VERDICT:APPROVED] or [VERDICT:REPROVED] markers
        verdicts = re.findall(r'\[VERDICT:(APPROVED|REPROVED)\]', text, re.IGNORECASE)
        if len(verdicts) == 0:
            return {"found": False, "error": "No [VERDICT:...] markers found in text"}
        if len(verdicts) == 1:
            return {
                "found": True,
                "partial": True,
                "verdicts": [verdicts[0].upper()],
                "warning": "Only 1 verdict found, validate gate requires 2 (PM + TL)"
            }
        # Take first two verdicts as PM, TL
        pm = verdicts[0].upper()
        tl = verdicts[1].upper()
        combined = "APPROVED" if pm == "APPROVED" and tl == "APPROVED" else "REPROVED"
        return {
            "found": True,
            "pm": pm,
            "tl": tl,
            "combined": combined,
            "combined_verdict": f"{pm},{tl}",
        }

    elif phase == "review":
        # Look for [GATE:PASS] or [GATE:FAIL]
        gates = re.findall(r'\[GATE:(PASS|FAIL)\]', text, re.IGNORECASE)
        if not gates:
            return {"found": False, "error": "No [GATE:PASS/FAIL] marker found in text"}
        verdict = gates[-1].upper()  # Take last one if multiple
        # Count blocking issues
        blocking = len(re.findall(r'(?i)(blocking|critical|must.?fix)', text))
        return {
            "found": True,
            "verdict": verdict,
            "blocking_issues_estimate": blocking,
        }

    elif phase == "test":
        # Look for [GATE:PASS], [GATE:FAIL_BUG], or [GATE:FAIL_TEST]
        gates = re.findall(r'\[GATE:(PASS|FAIL_BUG|FAIL_TEST)\]', text, re.IGNORECASE)
        if not gates:
            return {"found": False, "error": "No [GATE:PASS/FAIL_BUG/FAIL_TEST] marker found"}
        verdict = gates[-1].upper()
        # Extract test summary if present
        passed = re.findall(r'(\d+)\s*(?:tests?\s+)?passed', text, re.IGNORECASE)
        failed = re.findall(r'(\d+)\s*(?:tests?\s+)?failed', text, re.IGNORECASE)
        return {
            "found": True,
            "verdict": verdict,
            "tests_passed": int(passed[-1]) if passed else None,
            "tests_failed": int(failed[-1]) if failed else None,
        }

    else:
        raise ValueError(f"Unknown gate phase: {phase}. Valid: validate, review, test")


def check_iteration(phase: str, iteration: int, max_iterations: int) -> dict:
    """Check if gate iteration limit has been reached."""
    should_escalate = iteration >= max_iterations
    return {
        "phase": phase,
        "iteration": iteration,
        "max": max_iterations,
        "should_escalate": should_escalate,
        "action": "escalate_to_user" if should_escalate else "continue_loop",
        "message": (
            f"Gate failed {iteration}/{max_iterations} times. Escalating to user."
            if should_escalate
            else f"Gate iteration {iteration}/{max_iterations}. Retrying."
        ),
    }


def extract_questions(text: str) -> dict:
    """Extract [QUESTIONS] blocks from agent output."""
    questions = []

    # Pattern 1: [QUESTIONS] block followed by numbered/bulleted items
    q_blocks = re.findall(
        r'\[QUESTIONS\]\s*(.*?)(?=\[(?:VERDICT|GATE|NOTES)\]|\Z)',
        text, re.DOTALL | re.IGNORECASE
    )
    for block in q_blocks:
        # Extract individual questions (numbered, bulleted, or line-by-line)
        for line in block.strip().splitlines():
            line = line.strip()
            # Remove leading markers: "1.", "- ", "* ", "Q:", etc.
            cleaned = re.sub(r'^(?:\d+[.)]\s*|[-*]\s*|Q\d*:\s*)', '', line).strip()
            # Skip lines that are verdict/gate markers
            if re.match(r'^\[(?:VERDICT|GATE|NOTES|QUESTION)', cleaned, re.IGNORECASE):
                continue
            if cleaned and len(cleaned) > 5 and cleaned.endswith('?'):
                questions.append(cleaned)
            elif cleaned and len(cleaned) > 10:
                # Accept non-question sentences that are substantial
                questions.append(cleaned)

    # Pattern 2: Inline [QUESTION: ...] markers
    inline = re.findall(r'\[QUESTION:\s*([^\]]+)\]', text, re.IGNORECASE)
    questions.extend(q.strip() for q in inline)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in questions:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)

    return {
        "found": len(unique) > 0,
        "count": len(unique),
        "questions": unique,
    }


def handle_gate(args: list[str]) -> dict:
    if not args:
        raise ValueError("Subcommand required: parse, check, extract-questions")

    subcmd = args[0]

    if subcmd == "extract-questions":
        parser = argparse.ArgumentParser(prog="agency_cli gate extract-questions")
        parser.add_argument("--file", help="Path to file containing agent output")
        parser.add_argument("--text", help="Direct text to parse")
        parser.add_argument("--text-stdin", action="store_true",
                            help="Read text from stdin (avoids shell escaping issues)")
        opts = parser.parse_args(args[1:])

        text = _resolve_text_input(opts)
        return extract_questions(text)

    elif subcmd == "parse":
        parser = argparse.ArgumentParser(prog="agency_cli gate parse")
        parser.add_argument("--file", help="Path to file containing agent output")
        parser.add_argument("--text", help="Direct text to parse")
        parser.add_argument("--text-stdin", action="store_true",
                            help="Read text from stdin (avoids shell escaping issues)")
        parser.add_argument("--phase", required=True, choices=["validate", "review", "test"])
        opts = parser.parse_args(args[1:])

        text = _resolve_text_input(opts)
        return parse_verdict_from_text(text, opts.phase)

    elif subcmd == "check":
        parser = argparse.ArgumentParser(prog="agency_cli gate check")
        parser.add_argument("--phase", required=True)
        parser.add_argument("--iteration", required=True, type=int)
        parser.add_argument("--max", default=3, type=int)
        opts = parser.parse_args(args[1:])
        return check_iteration(opts.phase, opts.iteration, opts.max)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}. Valid: parse, check")
