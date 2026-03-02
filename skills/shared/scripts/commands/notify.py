"""
agency_cli notify -- Windows toast notifications for the SDLC Agency.

Usage:
    agency_cli notify send --title <text> --message <text> [--silent]
    agency_cli notify phase-complete --state-path <path> --phase <phase>
    agency_cli notify sdlc-complete --state-path <path>
    agency_cli notify input-needed [--agent <name>]
"""

import argparse
import json
import os
import platform
import subprocess
import sys


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _send_toast(title: str, message: str, sound: bool = True) -> dict:
    """Send a Windows toast notification. Returns status dict."""
    if not _is_windows():
        return {"status": "skipped", "reason": "not_windows", "platform": platform.system()}

    safe_title = (title.replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))
    safe_message = (message.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;"))

    audio_xml = '<audio silent="true"/>' if not sound else ""

    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{safe_title}</text>
      <text>{safe_message}</text>
    </binding>
  </visual>
  {audio_xml}
</toast>
"@
$XmlDocument = [Windows.Data.Xml.Dom.XmlDocument]::New()
$XmlDocument.LoadXml($xml)
$AppId = '{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($XmlDocument)
Write-Output "OK"
'''

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and "OK" in result.stdout:
            return {"status": "sent", "title": title}
        return {"status": "error", "returncode": result.returncode,
                "stderr": result.stderr.strip()[:200]}
    except FileNotFoundError:
        return {"status": "skipped", "reason": "powershell_not_found"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "timeout"}


def _load_state(state_path: str) -> dict:
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def send_direct(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli notify send")
    parser.add_argument("--title", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--silent", action="store_true")
    opts = parser.parse_args(args)
    return _send_toast(opts.title, opts.message, sound=not opts.silent)


def notify_phase_complete(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli notify phase-complete")
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--phase", required=True)
    opts = parser.parse_args(args)

    state = _load_state(opts.state_path)
    project = state.get("project", "Project")
    completed = state.get("metrics", {}).get("completed_phases", 0)
    total = state.get("metrics", {}).get("total_phases", 7)
    phase = opts.phase.title()

    # Check if phase had a gate
    phase_obj = state.get("phases", {}).get(opts.phase.lower(), {})
    gate_info = ""
    if "gate" in phase_obj and phase_obj["gate"].get("verdicts"):
        last = phase_obj["gate"]["verdicts"][-1]
        verdict = last.get("combined") or last.get("verdict", "")
        gate_info = f" | Gate: {verdict}"

    return _send_toast(
        f"{project} — {phase} Complete ({completed}/{total})",
        f"Phase {phase} finished successfully.{gate_info}"
    )


def notify_sdlc_complete(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli notify sdlc-complete")
    parser.add_argument("--state-path", required=True)
    opts = parser.parse_args(args)

    state = _load_state(opts.state_path)
    project = state.get("project", "Project")
    gate_iters = state.get("metrics", {}).get("total_gate_iterations", 0)

    # Calculate total duration
    durations = state.get("metrics", {}).get("phase_durations", {})
    total_secs = sum(durations.values())
    mins = total_secs // 60
    secs = total_secs % 60

    return _send_toast(
        f"✅ {project} — SDLC Complete!",
        f"All 7 phases done in {mins}m{secs}s. Gate iterations: {gate_iters}.",
        sound=True
    )


def notify_input_needed(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="agency_cli notify input-needed")
    parser.add_argument("--agent", required=False, default=None)
    opts = parser.parse_args(args)

    if opts.agent:
        title = f"🏗️ Agency — {opts.agent} needs input"
    else:
        title = "🏗️ Agency — Input Needed"

    return _send_toast(
        title,
        "The orchestrator is waiting for your input. Check Claude Code.",
        sound=True
    )


def handle_notify(args: list[str]) -> dict:
    if not args:
        raise ValueError(
            "Subcommand required: send, phase-complete, sdlc-complete, input-needed"
        )

    subcmd = args[0]

    if subcmd == "send":
        return send_direct(args[1:])
    elif subcmd == "phase-complete":
        return notify_phase_complete(args[1:])
    elif subcmd == "sdlc-complete":
        return notify_sdlc_complete(args[1:])
    elif subcmd == "input-needed":
        return notify_input_needed(args[1:])
    else:
        raise ValueError(
            f"Unknown subcommand: {subcmd}. "
            "Valid: send, phase-complete, sdlc-complete, input-needed"
        )
