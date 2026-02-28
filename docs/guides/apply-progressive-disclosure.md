# apply-progressive-disclosure

Analyzes and restructures Claude Code configuration files (`CLAUDE.md`, `SKILL.md`) to reduce token consumption. Large configuration files load into every conversation turn — this skill fragments them into hierarchical, lazy-loaded structures so only the relevant parts are loaded when needed.

## When to use

- `CLAUDE.md` has grown large and is consuming a significant portion of the context window on every turn
- A `SKILL.md` is slow to trigger because of its size
- After running `repo-map` or `project-map` to validate and optimize the generated docs
- Periodically as a project evolves and documentation accumulates

## Invocation

```
/omni-sw:apply-progressive-disclosure [analyze|optimize|report] [path] [--dry-run]
```

Without an argument, defaults to `analyze` on the current working directory.

## Commands

### `analyze`

Scans the target and produces a token budget report at `docs/CONTEXT_ANALYSIS.md`. Shows which files consume the most tokens at startup and the top recommendations for reduction.

```
/omni-sw:apply-progressive-disclosure analyze
/omni-sw:apply-progressive-disclosure analyze /path/to/skill-dir
```

**Run this first** before optimizing. Review the report to understand where tokens are being spent.

### `optimize`

Applies progressive disclosure transformations: fragments large files into referenced sub-documents, extracts long code blocks to scripts, converts complex procedures into separate skill files, and builds an index table.

```
/omni-sw:apply-progressive-disclosure optimize
/omni-sw:apply-progressive-disclosure optimize --dry-run
```

Use `--dry-run` to preview all changes without writing any files. The skill asks for confirmation before applying if changes affect more than 5 files.

### `report`

Generates a before/after comparison of token usage, showing the reduction achieved per file and the total startup cost change.

```
/omni-sw:apply-progressive-disclosure report
```

Requires that `analyze` and `optimize` have already been run (it reads the saved analysis files).

## Target detection

The skill automatically detects whether it is running on a project root (contains `CLAUDE.md`) or a skill directory (contains `SKILL.md`) and applies the appropriate thresholds and rules.

## What it transforms

| Priority | Transformation | Condition |
|----------|---------------|-----------|
| 1 | Fragment `CLAUDE.md` / `SKILL.md` into sub-documents under `agent_docs/` or `references/` | File exceeds 300 tokens |
| 2 | Extract code blocks to `scripts/` | Code block > 50 lines |
| 3 | Convert step-by-step procedures to separate skill files | Procedure > 10 steps |
| 4 | Build documentation index table in the root file | After extraction |
| 5 | Deduplicate content across files | Duplicate blocks found |

## Protected content

These sections are **never fragmented** out of `CLAUDE.md`, regardless of size:

- Build and test commands (top 5 most-used)
- Environment variable and secret handling instructions
- Security rules
- Stack declaration
- Directory structure overview
- The documentation index table itself

## Recommended workflow

```
/omni-sw:apply-progressive-disclosure analyze      # 1. See where tokens are spent
/omni-sw:apply-progressive-disclosure optimize --dry-run  # 2. Preview changes
/omni-sw:apply-progressive-disclosure optimize     # 3. Apply
/omni-sw:apply-progressive-disclosure report       # 4. Verify savings
```

## Tips

- This skill is called automatically by `repo-map` and `project-map` after generating documentation — no need to run it manually after those skills unless you want to re-optimize later.
- Run `analyze` after significant changes to `CLAUDE.md` to catch new bloat early.
- The `--dry-run` flag is safe to run anytime and produces no side effects.
