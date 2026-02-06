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

**Workflow (Project mode):**

1. Locate the project root (directory containing `CLAUDE.md`). If the working directory has no `CLAUDE.md`, ask the user for the project path.

2. Scan for all Claude Code configuration files:
   - `CLAUDE.md` (root and subdirectories)
   - `CLAUDE.local.md`
   - `.claude/settings.json`
   - `.claude/commands/*.md`
   - `.claude/skills/*/SKILL.md`
   - Any `agent_docs/` directory

3. For each file, estimate tokens: `ceil(character_count / 4)`.

4. Identify startup cost: files loaded on every session (CLAUDE.md files in the path hierarchy).

5. Detect fragmentation candidates using thresholds from `references/fragmentation-rules.md`:
   - Files >500 tokens: candidate
   - Files >1000 tokens: recommended
   - Files >2000 tokens: mandatory
   - Sections >300 tokens within a file: candidate for extraction
   - Procedural blocks >10 steps: convert to skill
   - Code blocks >50 lines: extract to script

6. Detect duplicate content across files (repeated paragraphs or instructions).

7. Produce the analysis report following the format in `references/report-format.md`. Write to `docs/CONTEXT_ANALYSIS.md` at the project root.

8. Present a summary to the user with the top 3 recommendations.

**Workflow (Skill mode):**

1. Confirm the target directory contains `SKILL.md`.

2. Scan all skill files:
   - `SKILL.md` (measure body separately from frontmatter)
   - `references/*.md`
   - `scripts/*`
   - `assets/*`

3. For each file, estimate tokens: `ceil(character_count / 4)`. For `SKILL.md`, also count body lines (excluding frontmatter delimiters and YAML content).

4. Identify trigger cost: tokens loaded when the skill activates = `SKILL.md` body tokens.

5. Detect fragmentation candidates using skill-specific thresholds from `references/fragmentation-rules.md`:
   - SKILL.md body > 500 lines: recommended to extract sections to `references/`
   - SKILL.md body > 2000 tokens: mandatory extraction
   - Reference file > 10,000 tokens: recommended split
   - Code block in SKILL.md > 30 lines: candidate for `scripts/`
   - Code block in SKILL.md > 50 lines: mandatory extraction to `scripts/`

6. Detect duplicate content between SKILL.md and reference files.

7. Write analysis report to `docs/CONTEXT_ANALYSIS.md` inside the skill directory.

8. Present a summary to the user with the top 3 recommendations.

## Mode: Optimize

Apply progressive disclosure transformations. Read `references/fragmentation-rules.md` for thresholds and rules.

**Workflow:**

1. If `docs/CONTEXT_ANALYSIS.md` exists, read it. Otherwise, run the Analyze workflow first.

2. If `--dry-run` flag is present: describe all changes that would be made without writing any files. Present the plan and ask for confirmation before proceeding.

3. Apply transformations in priority order:

   **Priority 1 — Fragment CLAUDE.md:**
   - Extract sections exceeding 300 tokens to `agent_docs/{section-slug}.md`
   - Keep in CLAUDE.md: project name, stack (1-2 lines), top 5 commands, documentation index table
   - Target: CLAUDE.md < 500 tokens, < 60 lines
   - Create `agent_docs/` directory if needed

   **Priority 2 — Extract code to scripts:**
   - Move code blocks >50 lines to `scripts/` or `.claude/scripts/`
   - Replace with one-line reference: "Run `scripts/{name}.{ext}`"

   **Priority 3 — Convert procedures to skills:**
   - Identify step-by-step instructions (>10 steps) that are self-contained workflows
   - Create skill files in `.claude/commands/` with frontmatter
   - Replace in source with: "Use `/command-name` for this workflow"

   **Priority 4 — Build documentation index:**
   - Add an index table to CLAUDE.md linking all extracted documents
   - Each row: document path, one-line description, when to load it
   - Add instruction: "Load only docs relevant to the current task."

   **Priority 5 — Deduplicate:**
   - Keep authoritative version in most specific location
   - Replace duplicates with reference to authoritative source

4. After applying changes, produce a migration report following `references/report-format.md`. Write to `docs/CONTEXT_MIGRATION.md`.

5. Present token savings summary to the user.

**Workflow (Skill mode — Optimize):**

1. If `docs/CONTEXT_ANALYSIS.md` exists inside the skill directory, read it. Otherwise, run Analyze (Skill mode) first.

2. If `--dry-run`: describe changes without writing. Ask confirmation before proceeding.

3. Apply transformations in priority order:

   **Priority 1 — Fragment SKILL.md body:**
   - Extract sections exceeding 300 tokens to `references/{section-slug}.md`
   - Keep in SKILL.md: frontmatter, workflow overview, argument declarations, references index
   - Target: SKILL.md body < 500 lines

   **Priority 2 — Extract code blocks to scripts:**
   - Move code blocks > 50 lines to `scripts/{name}.ext`
   - Replace with: "Run `scripts/{name}.ext`"
   - Code blocks > 30 lines: evaluate case-by-case (extract if reusable)

   **Priority 3 — Split large reference files:**
   - Reference files > 10,000 tokens: split by logical section into multiple files
   - Add a table of contents to files > 100 lines

   **Priority 4 — Add references index to SKILL.md:**
   - If not present, add an index listing all reference files with "when to load" triggers

   **Priority 5 — Deduplicate:**
   - Remove content duplicated between SKILL.md and reference files
   - Keep detailed version in references, keep summary in SKILL.md

4. Write migration report to `docs/CONTEXT_MIGRATION.md` inside the skill directory.

5. Present token savings summary.

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
