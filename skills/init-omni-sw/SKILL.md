---
name: init-omni-sw
description: >-
  Project Setup for Omni-SW Agency — Configures a project directory with all base files
  and hooks required by the SDLC Agency plugin before the orchestrator can run.
  Creates CLAUDE.md, agent_docs/ directories, notification hooks, and validates the
  environment. Use when: (1) setting up a new project for the agency (/init-omni-sw),
  (2) user says "setup", "configure project", "init project", "prepare project for agency",
  "install hooks", "configure hooks", "setup omni-sw", "configure plugin", or
  (3) before running the orchestrator for the first time on a project. This skill should
  also trigger when the user wants to verify or fix the agency configuration in an
  existing project.
argument-hint: <path to project root directory>
---

# Omni-SW Project Setup

Configure a project directory for the SDLC Agency. This runs in the main session (not as a subagent) so that `AskUserQuestion` works correctly.

## Step 1: Resolve the CLI Path

Find this skill's own SKILL.md to derive the CLI path:

```
Glob pattern: "**/init-omni-sw/SKILL.md"
```

From the SKILL.md path, the CLI is at `../../shared/scripts/agency_cli.py` relative to the `init-omni-sw/` directory.

Verify it exists with `ls`, then store the resolved path as `{CLI}`.

## Step 2: Determine What Exists

If the user provided a path as argument, use that as `{PROJECT_ROOT}`. Otherwise, use the current working directory.

Check the directory contents:

```bash
ls -la "{PROJECT_ROOT}" 2>&1
```

### Case A: Empty directory (no files, or only `.git`)

Use `AskUserQuestion` to collect project details. Ask all in a single call:

- **Project type** — Web API, Console App, Blazor, Library, other?
- **Project name** — What should the project be called?
- **Stack** — Technology stack (e.g., .NET 9, Node.js + TypeScript, Python + FastAPI)
- **Include tests?** — Yes or No

Then run the setup command with the answers:

```bash
MSBUILD_EXE_PATH="" python "{CLI}" setup --scan-root "{PROJECT_ROOT}" --name "{name}" --stack "{stack}" --type "{type}" [--no-tests]
```

### Case B: Non-empty directory without CLAUDE.md

The project has code but no CLAUDE.md. Use the `/repo-map` skill to scan the codebase first:

```
/repo-map {PROJECT_ROOT}
```

The repo-map will discover the stack, structure, and generate `CLAUDE.md`. After it completes, run setup to create directories and hooks:

```bash
MSBUILD_EXE_PATH="" python "{CLI}" setup --scan-root "{PROJECT_ROOT}"
```

### Case C: Non-empty directory WITH CLAUDE.md

The project already has a CLAUDE.md. Just run setup to ensure directories and hooks are in place:

```bash
MSBUILD_EXE_PATH="" python "{CLI}" setup --scan-root "{PROJECT_ROOT}"
```

## Step 3: Verify and Report

After setup completes, run verify to confirm everything is ready:

```bash
MSBUILD_EXE_PATH="" python "{CLI}" setup --scan-root "{PROJECT_ROOT}" --verify
```

Report the results to the user. Pay attention to the `hooks` status:

- If hooks were just created (`"action": "created"` or `"action": "merged"`), tell the user:
  > Hooks were installed. To activate them, either:
  > 1. Run `/hooks` in Claude Code and approve the notification hook, OR
  > 2. Start a new Claude Code session (hooks load at startup)
  >
  > Then run `/orchestrator "<objective>"` to start the SDLC.

- If hooks were already installed (`"action": "already_installed"`):
  > Everything is ready. Run `/orchestrator "<objective>"` to start.
