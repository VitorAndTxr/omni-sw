#!/usr/bin/env python3
"""
Windows toast notification utility for the SDLC Agency.

Sends native Windows 10/11 toast notifications via PowerShell.
No external dependencies — uses PowerShell's built-in WinRT APIs.

Usage:
    # Direct invocation
    python notify.py --title "Title" --message "Body text" [--sound]

    # As a Claude Code hook (reads JSON from stdin)
    echo '{"tool_name":"AskUserQuestion",...}' | python notify.py --hook

    # Completion notification (reads STATE.json for summary)
    python notify.py --completion --state-path <path-to-STATE.json>

Exit codes:
    0 — notification sent (or silently skipped on non-Windows)
    1 — error
    Note: NEVER exits with code 2 (does not block tool execution)
"""

import argparse
import json
import os
import platform
import subprocess
import sys


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def send_notification(title: str, message: str, sound: bool = True) -> bool:
    """Send a Windows toast notification via PowerShell.

    Uses native WinRT APIs available in Windows PowerShell 5.1+.
    Returns True if notification was sent, False otherwise.
    """
    if not is_windows():
        # Silent no-op on non-Windows (e.g., WSL, Linux CI)
        print(json.dumps({
            "status": "skipped",
            "reason": "not_windows",
            "platform": platform.system(),
        }))
        return False

    # Escape XML special characters
    safe_title = (title
                  .replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;")
                  .replace("'", "&apos;"))
    safe_message = (message
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;"))

    # Build toast XML
    audio_xml = ""
    if sound:
        audio_xml = '<audio src="ms-winsoundevent:Notification.Default"/>'
    else:
        audio_xml = '<audio silent="true"/>'

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
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and "OK" in result.stdout:
            print(json.dumps({"status": "sent", "title": title}))
            return True
        else:
            print(json.dumps({
                "status": "error",
                "returncode": result.returncode,
                "stderr": result.stderr.strip()[:200],
            }), file=sys.stderr)
            return False

    except FileNotFoundError:
        print(json.dumps({
            "status": "skipped",
            "reason": "powershell_not_found",
        }))
        return False
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "status": "error",
            "reason": "timeout",
        }), file=sys.stderr)
        return False


def handle_hook_mode():
    """Handle Claude Code hook mode: read stdin JSON, send simple alert notification.

    Designed for PreToolUse hooks on AskUserQuestion — notifies user that
    the orchestrator needs input. The actual question appears in the Claude
    Code chat, so the notification is just an alert to check the terminal.
    Does not block the tool call (exit 0).
    """
    try:
        # Consume stdin (required by hook protocol) but don't use content
        sys.stdin.read()
        send_notification(
            "🏗️ Agency — Input Needed",
            "The orchestrator is waiting for your input. Check Claude Code."
        )
    except Exception:
        # Silently ignore errors — do not block tool execution
        pass


def handle_completion_mode(state_path: str):
    """Send a completion notification with summary from STATE.json."""
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        project = state.get("project", "Project")
        completed = state.get("metrics", {}).get("completed_phases", 0)
        total = state.get("metrics", {}).get("total_phases", 7)
        overall = state.get("status", "unknown")
        gate_iters = state.get("metrics", {}).get("total_gate_iterations", 0)

        if overall == "completed":
            title = f"✅ {project} — SDLC Complete"
            message = f"All {total} phases completed. Gate iterations: {gate_iters}."
        else:
            title = f"🏗️ {project} — Phase {completed}/{total}"
            current = state.get("current_phase", "unknown")
            message = f"Current: {current}. Gate iterations: {gate_iters}."

        send_notification(title, message, sound=True)

    except FileNotFoundError:
        print(json.dumps({"status": "error", "reason": "state_file_not_found"}), file=sys.stderr)
    except (json.JSONDecodeError, KeyError) as e:
        print(json.dumps({"status": "error", "reason": str(e)}), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog="notify",
        description="Send Windows toast notifications for the SDLC Agency."
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--hook", action="store_true",
                      help="Hook mode: read Claude Code hook JSON from stdin")
    mode.add_argument("--title", type=str,
                      help="Direct mode: notification title")
    mode.add_argument("--completion", action="store_true",
                      help="Completion mode: send summary from STATE.json")

    parser.add_argument("--message", type=str, default="",
                        help="Notification body text (direct mode)")
    parser.add_argument("--state-path", type=str,
                        help="Path to STATE.json (completion mode)")
    parser.add_argument("--sound", action="store_true", default=True,
                        help="Play notification sound (default: true)")
    parser.add_argument("--silent", action="store_true",
                        help="Suppress notification sound")

    args = parser.parse_args()

    if args.hook:
        handle_hook_mode()
    elif args.completion:
        if not args.state_path:
            print("Error: --state-path required for completion mode", file=sys.stderr)
            sys.exit(1)
        handle_completion_mode(args.state_path)
    elif args.title:
        sound = not args.silent
        send_notification(args.title, args.message, sound=sound)


if __name__ == "__main__":
    main()
