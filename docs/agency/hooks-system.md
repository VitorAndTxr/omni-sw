# Hooks System

Automated guardrails that execute in response to Claude Code tool events. Hooks are project-level and defined in each project's `.claude/hooks.json`.

## Agency notification hook

The agency ships a built-in notification hook that fires a Windows toast whenever the orchestrator needs user input. It is installed automatically by `/omni-sw:init-omni-sw` or `agency_cli setup`.

**Event:** `PreToolUse` on `AskUserQuestion`
**Command:** `python "<plugin>/scripts/notify.py" --hook`
**Behavior:** reads stdin (required by the hook protocol), sends a toast, exits 0 (never blocks the tool call).

Template at `scripts/hooks/hooks-template.json` — replace `<PLUGIN_PATH>` before use:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "AskUserQuestion",
        "hooks": [
          {
            "type": "command",
            "command": "python <PLUGIN_PATH>/scripts/notify.py --hook",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Hooks take effect at the start of the **next Claude Code session**. To activate immediately, run `/hooks` in Claude Code and approve the new entry.

## Advisory hooks (examples)

**PostToolUse -- Edit|Write matcher:**
Triggers after any Edit or Write tool call. Checks if the file path ends in `.cs` or `.csproj`. If so, prints a reminder to stderr: `[hook:type-check] C# file changed -- consider running: dotnet build`. Exit code 0 (advisory only).

**PreToolUse -- Bash matcher:**
Triggers before any Bash tool call. Checks if the command contains `git commit`. If so, prints a reminder to stderr: `[hook:test-guard] Commit detected -- ensure tests pass before committing.` Exit code 0 (advisory only).

## Hook Configuration Format

```json
{
  "hooks": {
    "<EventType>": [
      {
        "matcher": "<ToolName|ToolName2>",
        "hooks": [
          {
            "type": "command",
            "command": "<shell command>",
            "timeout": 5,
            "description": "<human-readable description>"
          }
        ]
      }
    ]
  }
}
```

## Valid Event Types

- `PreToolUse` -- Runs before a tool is executed. Receives tool input via stdin as JSON.
- `PostToolUse` -- Runs after a tool is executed. Receives tool input via stdin as JSON.

## Matcher Syntax

The `matcher` field is a pipe-separated list of tool names (e.g., `"Edit|Write"`, `"Bash"`). It matches when the tool being invoked matches any of the listed names.

## Stdin/Stdout Protocol

Hook commands receive the tool invocation data on stdin as JSON. The shape includes a `tool_input` object with the parameters passed to the tool (e.g., `file_path` for Edit/Write, `command` for Bash). Hooks communicate back via stderr (advisory messages) and exit codes. Exit code 0 means the tool call proceeds. A non-zero exit code blocks the tool call.

## Extending Hooks

To add a new hook:

1. Choose the event type (`PreToolUse` or `PostToolUse`).
2. Define the matcher (which tools trigger it).
3. Write a shell command that reads stdin JSON (use `jq` to extract fields).
4. Set `timeout` (seconds) to prevent hangs.
5. Use exit code 0 for advisory hooks, non-zero to block the action.

Example -- lint check after TypeScript file edits:

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "INPUT=$(cat); FILE=$(echo \"$INPUT\" | jq -r '.tool_input.file_path // empty'); if [ -n \"$FILE\" ] && echo \"$FILE\" | grep -qE '\\.(ts|tsx)$'; then echo '[hook:lint] TypeScript file changed — consider running: npm run lint' >&2; fi; exit 0",
      "timeout": 5,
      "description": "Remind to lint after TypeScript file edits"
    }
  ]
}
```
