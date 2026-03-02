"""
agency_cli setup -- Full project setup for the SDLC Agency.

Combines CLAUDE.md creation, directory setup, and hook installation into a single
deterministic command. Accepts all project details as flags so it can be called
from the main Claude Code session (where AskUserQuestion works) without needing
to run as a skill/subagent.

Usage:
    # Full setup with project details:
    agency_cli setup --scan-root <path> --name "MyProject" --stack ".NET 9" --type "Web API"

    # Setup with existing CLAUDE.md (skip creation):
    agency_cli setup --scan-root <path>

    # Verify-only mode (no changes):
    agency_cli setup --scan-root <path> --verify
"""

import argparse
import json
import os
import textwrap

from init_cmd import find_claude_md, find_backlog_script, derive_team_name, install_hooks


def create_claude_md(project_root: str, name: str, stack: str, project_type: str,
                     conventions: str = "", tests: bool = True) -> str:
    """Create a CLAUDE.md file with project metadata. Returns the file path."""

    # Derive build/test commands from stack
    stack_lower = stack.lower() if stack else ""
    if ".net" in stack_lower or "dotnet" in stack_lower or "c#" in stack_lower:
        build_cmd = "dotnet build"
        test_cmd = "dotnet test" if tests else "N/A"
        lang = "C#"
    elif "node" in stack_lower or "typescript" in stack_lower or "javascript" in stack_lower:
        build_cmd = "npm run build"
        test_cmd = "npm test" if tests else "N/A"
        lang = "TypeScript" if "typescript" in stack_lower else "JavaScript"
    elif "python" in stack_lower:
        build_cmd = "pip install -e ."
        test_cmd = "pytest" if tests else "N/A"
        lang = "Python"
    else:
        build_cmd = "TBD"
        test_cmd = "TBD" if tests else "N/A"
        lang = ""

    conventions_line = f"- {conventions}" if conventions else "- TBD"
    lang_line = f"- Language: {lang}\n" if lang else ""

    content = f"""# Project: {name}

## Stack
- {stack}
- Type: {project_type}

## Conventions
{lang_line}{conventions_line}

## Commands
- Build: `{build_cmd}`
- Test: `{test_cmd}`
"""

    filepath = os.path.join(project_root, "CLAUDE.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def verify_setup(scan_root: str) -> dict:
    """Verify project setup without making changes."""
    scan_root = os.path.normpath(os.path.abspath(scan_root))
    project_root = find_claude_md(scan_root)

    result = {
        "project_root": project_root,
        "checks": {}
    }

    if not project_root:
        result["checks"]["claude_md"] = {"status": "missing", "ok": False}
        result["checks"]["directories"] = {"status": "unknown", "ok": False}
        result["checks"]["hooks"] = {"status": "unknown", "ok": False}
        result["overall"] = "not_configured"
        return result

    # Check CLAUDE.md
    claude_md = os.path.join(project_root, "CLAUDE.md")
    result["checks"]["claude_md"] = {
        "status": "exists" if os.path.isfile(claude_md) else "missing",
        "ok": os.path.isfile(claude_md),
    }

    # Check directories
    backlog_dir = os.path.join(project_root, "agent_docs", "backlog")
    agency_dir = os.path.join(project_root, "agent_docs", "agency")
    dirs_ok = os.path.isdir(backlog_dir) and os.path.isdir(agency_dir)
    result["checks"]["directories"] = {
        "status": "exists" if dirs_ok else "missing",
        "ok": dirs_ok,
        "backlog_dir": os.path.isdir(backlog_dir),
        "agency_dir": os.path.isdir(agency_dir),
    }

    # Check hooks
    hooks_file = os.path.join(project_root, ".claude", "hooks.json")
    if os.path.isfile(hooks_file):
        try:
            with open(hooks_file, 'r', encoding='utf-8') as f:
                hooks_data = json.load(f)
            pre_tool = hooks_data.get("hooks", {}).get("PreToolUse", [])
            has_ask = any(
                isinstance(h, dict) and h.get("matcher") == "AskUserQuestion"
                for h in pre_tool
            )
            result["checks"]["hooks"] = {
                "status": "installed" if has_ask else "missing_matcher",
                "ok": has_ask,
            }
        except (json.JSONDecodeError, IOError):
            result["checks"]["hooks"] = {"status": "corrupted", "ok": False}
    else:
        result["checks"]["hooks"] = {"status": "missing", "ok": False}

    # Check backlog
    script_path = find_backlog_script(scan_root)
    backlog_path = os.path.join(project_root, "agent_docs", "backlog", "backlog.json")
    result["checks"]["backlog_api"] = {
        "status": "available" if script_path else "not_found",
        "ok": script_path is not None,
        "script_path": script_path,
        "backlog_exists": os.path.isfile(backlog_path),
    }

    all_ok = all(c["ok"] for c in result["checks"].values())
    result["overall"] = "ready" if all_ok else "incomplete"
    result["team_name"] = derive_team_name(project_root)

    return result


def handle_setup(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli setup")
    parser.add_argument("--scan-root", required=True, help="Root directory of the project")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--stack", help="Technology stack (e.g., '.NET 9', 'Node.js + TypeScript')")
    parser.add_argument("--type", dest="project_type", help="Project type (e.g., 'Web API', 'Console', 'Blazor')")
    parser.add_argument("--conventions", default="", help="Conventions to follow")
    parser.add_argument("--tests", action="store_true", default=True, help="Include test project (default: yes)")
    parser.add_argument("--no-tests", action="store_true", help="Do not include test project")
    parser.add_argument("--verify", action="store_true", help="Verify-only mode — check setup without changes")
    parser.add_argument("--no-hooks", action="store_true", help="Skip hook installation")
    opts = parser.parse_args(args)

    scan_root = os.path.normpath(os.path.abspath(opts.scan_root))
    if not os.path.isdir(scan_root):
        raise FileNotFoundError(f"Scan root not found: {scan_root}")

    # Verify-only mode
    if opts.verify:
        return verify_setup(scan_root)

    result = {"steps": []}
    include_tests = not opts.no_tests

    # Step 1: CLAUDE.md
    project_root = find_claude_md(scan_root)
    if project_root:
        result["steps"].append({
            "step": "claude_md",
            "action": "exists",
            "path": os.path.join(project_root, "CLAUDE.md"),
        })
    else:
        # Need project details to create CLAUDE.md
        if not opts.name:
            # Derive from directory name
            opts.name = os.path.basename(scan_root)
        if not opts.stack:
            opts.stack = "TBD"
        if not opts.project_type:
            opts.project_type = "TBD"

        project_root = scan_root
        claude_path = create_claude_md(
            project_root, opts.name, opts.stack, opts.project_type,
            opts.conventions, include_tests
        )
        result["steps"].append({
            "step": "claude_md",
            "action": "created",
            "path": claude_path,
        })

    # Step 2: Directories
    backlog_dir = os.path.join(project_root, "agent_docs", "backlog")
    agency_dir = os.path.join(project_root, "agent_docs", "agency")
    os.makedirs(backlog_dir, exist_ok=True)
    os.makedirs(agency_dir, exist_ok=True)
    result["steps"].append({
        "step": "directories",
        "action": "created",
        "backlog_dir": backlog_dir,
        "agency_dir": agency_dir,
    })

    # Step 3: Hooks
    if not opts.no_hooks:
        try:
            hooks_result = install_hooks(project_root)
            result["steps"].append({
                "step": "hooks",
                **hooks_result,
            })
        except Exception as e:
            result["steps"].append({
                "step": "hooks",
                "action": "error",
                "error": str(e),
            })
    else:
        result["steps"].append({"step": "hooks", "action": "skipped"})

    # Summary
    script_path = find_backlog_script(scan_root)
    backlog_path = os.path.join(project_root, "agent_docs", "backlog", "backlog.json")
    result["project_root"] = project_root
    result["team_name"] = derive_team_name(project_root)
    result["backlog_api"] = script_path is not None
    result["backlog_exists"] = os.path.isfile(backlog_path)
    result["script_path"] = script_path
    result["backlog_path"] = backlog_path

    return result
