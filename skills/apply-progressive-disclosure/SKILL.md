---
name: apply-progressive-disclosure
description: >-
  Progressive Disclosure Optimizer — Analyze and restructure Claude Code configuration
  files (CLAUDE.md, skills, commands, agents) to minimize token consumption. Supports
  both project roots (CLAUDE.md) and skill directories (SKILL.md). Applies hierarchical
  fragmentation, content indexing, skill extraction, and script extraction to reduce
  startup/trigger context cost. Use when: (1) analyzing repository token budget
  (/apply-progressive-disclosure analyze), (2) optimizing CLAUDE.md or SKILL.md for
  token efficiency (/apply-progressive-disclosure optimize), (3) generating before/after
  token reports (/apply-progressive-disclosure report), (4) optimizing a skill directory
  (/apply-progressive-disclosure analyze <skill-path>), or (5) user says "optimize context",
  "reduce tokens", "progressive disclosure", "context bloat", "token budget",
  "fragment CLAUDE.md", "optimize skill".
argument-hint: analyze | optimize [--dry-run] | report [<path>]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Progressive Disclosure Optimizer

Reduce tokens loaded at startup by fragmenting monolithic Claude Code configuration into hierarchical, lazy-loaded structures.

## Command Routing

Read the argument after `/apply-progressive-disclosure`. Route to the matching mode:

- `analyze` — Scan repository or skill, calculate token metrics, produce diagnostic report
- `optimize` — Apply fragmentation and restructuring (add `--dry-run` to preview without changes)
- `report` — Generate before/after comparison of token usage

If no argument: run `analyze` by default.

## Agency CLI Integration

This skill uses `agency_cli.py` for all deterministic token analysis operations:

Resolve CLI path via Glob: `**/shared/scripts/agency_cli.py`. Store result as `{CLI}`.

## Target Detection

Before executing any mode, determine the target type:

1. If a path argument is provided, use it. Otherwise use the working directory.
2. Check the target directory:
   - **Project mode:** Directory contains `CLAUDE.md` → analyze as project root
   - **Skill mode:** Directory contains `SKILL.md` → analyze as skill directory
   - **Neither:** Ask the user for the correct path

Skill mode uses skill-specific thresholds and targets from `references/fragmentation-rules.md` (see "Skill Directory" section).

## Mode: Analyze

Scan the target and produce a token budget report.

**Workflow (both modes):**

Use the CLI for the entire analysis — it handles project vs skill mode automatically:

```bash
# Run full token analysis
python {CLI} tokens analyze --root <target-path>
# Returns JSON: files, total_tokens, startup_tokens, fragmentation_candidates, etc.

# Find duplicate content
python {CLI} tokens deduplicate --root <target-path>
# Returns: duplicates with locations and token counts

# Generate the analysis report
python {CLI} report context-analysis --input <analysis-json> --output <target-path>/docs/CONTEXT_ANALYSIS.md
```

Present a summary to the user with the top 3 recommendations from the analysis output.

## Mode: Optimize

Apply progressive disclosure transformations. Read `references/fragmentation-rules.md` for thresholds and rules.

**Workflow (Project mode):**

Use CLI for deterministic fragmentation:

```bash
# Fragment CLAUDE.md (Priority 1)
python {CLI} tokens fragment --file <root>/CLAUDE.md --threshold 300 --output-dir <root>/agent_docs/ [--dry-run]

# Fragment a SKILL.md (Priority 1, skill mode)
python {CLI} tokens fragment-skill --file <path>/SKILL.md --threshold 300 --output-dir <path>/references/ [--dry-run]
```

After CLI handles the mechanical extraction, apply these judgment-based steps manually:

1. **Priority 2 — Extract code to scripts:** Review CLI output for code blocks >50 lines and move to `scripts/`.
2. **Priority 3 — Convert procedures to skills:** Identify step-by-step instructions (>10 steps) and create skill files.
3. **Priority 4 — Build documentation index:** Add index table to CLAUDE.md linking extracted documents.
4. **Priority 5 — Deduplicate:** Use `python {CLI} tokens deduplicate --root <path>` to find duplicates, then resolve manually.

After applying changes:
```bash
# Generate before/after comparison report
python {CLI} tokens report --before <before-analysis.json> --after <after-analysis.json> --output <root>/docs/CONTEXT_REPORT.md
```

Present token savings summary to the user.

**Constraints (both modes):**
- Never delete original content — only move it
- Preserve Claude Code precedence hierarchy (org > project > subdir > local)
- Do not fragment security rules, environment config, or essential build commands
- In skill mode: never extract frontmatter, workflow overview, or argument declarations
- Ask user confirmation before writing if changes affect >5 files

## Mode: Report

Generate a comparison report of token usage.

**Workflow (both modes):**

1. Locate `docs/CONTEXT_ANALYSIS.md` and `docs/CONTEXT_MIGRATION.md` in the target directory (project root or skill directory). If either is missing, inform the user which step to run first.

2. Re-scan current state to get live token counts.

3. Produce a diff report:
   - Before vs after token counts per file
   - Startup/trigger cost reduction percentage
   - Total configuration token change
   - List of files created, moved, or modified

4. Write to `docs/CONTEXT_REPORT.md` in the target directory and display summary.

## Protected Content

Never fragment or move these out of CLAUDE.md root, regardless of size:

- Build/test commands (top 5 most-used)
- Environment/secret handling instructions
- Security rules
- Stack declaration
- Directory structure overview
- Documentation index table itself
