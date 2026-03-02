"""
agency_cli init -- Resolve project paths and initialize environment.

Usage:
    agency_cli init --scan-root <path>
    agency_cli init --scan-root <path> --create-dirs

Resolves PROJECT_ROOT, SCRIPT_PATH, BACKLOG_PATH, TEAM_NAME deterministically.
Also installs Claude Code hooks for automatic notifications.
"""

import argparse
import glob
import os
import json
import copy


def find_claude_md(scan_root: str) -> str | None:
    """Find CLAUDE.md at [businessUnit]/[project]/ level."""
    for root, dirs, files in os.walk(scan_root):
        # Skip hidden dirs and common non-project dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in (
            'node_modules', 'bin', 'obj', 'dist', 'build', '__pycache__', 'venv', '.venv'
        )]
        if 'CLAUDE.md' in files:
            return root
    return None


def find_backlog_script(scan_root: str) -> str | None:
    """Find backlog_manager.py via glob pattern."""
    pattern = os.path.join(scan_root, '**', 'backlog', 'scripts', 'backlog_manager.py')
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return matches[0]
    # Fallback: broader search
    pattern2 = os.path.join(scan_root, '**', 'backlog_manager.py')
    matches2 = glob.glob(pattern2, recursive=True)
    return matches2[0] if matches2 else None


def derive_team_name(project_root: str) -> str:
    """Derive team name from project directory: agency-{basename}."""
    basename = os.path.basename(os.path.normpath(project_root))
    return f"agency-{basename}"


def get_plugin_root() -> str:
    """Derive the plugin root directory from this file's location.

    init_cmd.py is at: <plugin>/skills/shared/scripts/commands/init_cmd.py
    Plugin root is 4 levels up.
    """
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
    )


def install_hooks(project_root: str) -> dict:
    """Install or merge notification hooks into the project's .claude/hooks.json.

    Non-destructive: if hooks.json already exists, merges the AskUserQuestion
    hook into the existing PreToolUse array without duplicating or overwriting
    other hooks.
    """
    plugin_root = get_plugin_root()
    notify_script = os.path.join(plugin_root, "scripts", "notify.py")

    # Normalize path separators for the command string
    notify_script_cmd = notify_script.replace("\\", "/")

    hook_entry = {
        "type": "command",
        "command": f"python \"{notify_script_cmd}\" --hook",
        "timeout": 10
    }

    ask_hook = {
        "matcher": "AskUserQuestion",
        "hooks": [hook_entry]
    }

    claude_dir = os.path.join(project_root, ".claude")
    hooks_file = os.path.join(claude_dir, "hooks.json")

    os.makedirs(claude_dir, exist_ok=True)

    result = {"hooks_file": hooks_file}

    if os.path.isfile(hooks_file):
        # Merge into existing hooks.json
        try:
            with open(hooks_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

        hooks = existing.setdefault("hooks", {})
        pre_tool = hooks.setdefault("PreToolUse", [])

        # Check if AskUserQuestion hook already exists
        already_installed = any(
            isinstance(h, dict) and h.get("matcher") == "AskUserQuestion"
            for h in pre_tool
        )

        if already_installed:
            result["action"] = "already_installed"
            return result

        pre_tool.append(ask_hook)

        with open(hooks_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        result["action"] = "merged"
    else:
        # Create new hooks.json
        hooks_data = {
            "hooks": {
                "PreToolUse": [ask_hook]
            }
        }
        with open(hooks_file, 'w', encoding='utf-8') as f:
            json.dump(hooks_data, f, indent=2, ensure_ascii=False)

        result["action"] = "created"

    return result


def handle_init(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli init")
    parser.add_argument("--scan-root", required=True, help="Root directory to scan")
    parser.add_argument("--create-dirs", action="store_true", help="Create agent_docs/backlog/ if missing")
    parser.add_argument("--no-hooks", action="store_true", help="Skip notification hook installation")
    opts = parser.parse_args(args)

    scan_root = os.path.normpath(os.path.abspath(opts.scan_root))
    if not os.path.isdir(scan_root):
        raise FileNotFoundError(f"Scan root not found: {scan_root}")

    project_root = find_claude_md(scan_root)
    if not project_root:
        raise FileNotFoundError(f"No CLAUDE.md found under {scan_root}")

    script_path = find_backlog_script(scan_root)
    backlog_path = os.path.join(project_root, "agent_docs", "backlog", "backlog.json")
    team_name = derive_team_name(project_root)

    if opts.create_dirs:
        backlog_dir = os.path.dirname(backlog_path)
        os.makedirs(backlog_dir, exist_ok=True)

    result = {
        "project_root": project_root,
        "script_path": script_path,
        "backlog_path": backlog_path,
        "team_name": team_name,
        "claude_md": os.path.join(project_root, "CLAUDE.md"),
        "backlog_exists": os.path.isfile(backlog_path),
        "claude_md_exists": os.path.isfile(os.path.join(project_root, "CLAUDE.md")),
    }

    if script_path is None:
        result["warning"] = "backlog_manager.py not found. Backlog operations will fail."

    # Auto-install notification hooks
    if not opts.no_hooks:
        try:
            hooks_result = install_hooks(project_root)
            result["hooks"] = hooks_result
        except Exception as e:
            result["hooks"] = {"action": "error", "error": str(e)}

    return result
