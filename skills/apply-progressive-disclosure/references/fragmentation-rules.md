# Fragmentation Rules

## Token Estimation

Estimate tokens as `ceil(character_count / 4)`. Count characters excluding leading/trailing whitespace per file.

## Thresholds

| Scope | Threshold | Action |
|-------|-----------|--------|
| File > 500 tokens | Candidate | Evaluate for fragmentation |
| File > 1000 tokens | Recommended | Fragment into sub-documents |
| File > 2000 tokens | Mandatory | Fragment immediately |
| Section > 300 tokens | Candidate | Extract to separate file |
| Procedural block > 10 steps | Recommended | Convert to skill command |
| Code block > 50 lines | Mandatory | Extract to script file |

## Never Fragment

Keep these in the root CLAUDE.md regardless of size:

- Build/test commands (the 5 most frequent)
- Environment configuration
- Security rules and secret handling
- Stack declaration (1-2 lines)
- Top-level directory structure
- Documentation index table

## Fragmentation Targets

### CLAUDE.md Root File

Target: <60 lines, <500 tokens. Structure:

```
# Project Name
One-line description with stack.

## Essential Commands
(max 5, most-used only)

## Documentation Index
| Doc | When to load |
|-----|--------------|
| @agent_docs/X.md | context trigger |

Load only docs relevant to the current task.
```

### Extracted Documents (agent_docs/)

Each fragment should be self-contained with:
- Clear title matching the index entry
- Scope statement (first line: what this doc covers)
- No cross-references to other fragments (flat hierarchy)

### Extracted Skills (.claude/commands/)

Convert procedural instructions (step-by-step guides) into skill commands:
- Frontmatter with `name` and `description`
- Steps as numbered workflow
- Reference external scripts where possible

### Extracted Scripts (scripts/ or .claude/scripts/)

Move executable code blocks out of documentation:
- One script per logical operation
- Include usage comment at top
- Reference from documentation by path only: "Run `scripts/X.py`"

### Skill Directory (SKILL.md)

When the target is a skill directory (contains `SKILL.md` instead of `CLAUDE.md`):

**Detection:** Directory contains `SKILL.md` at root. No `CLAUDE.md` required.

**Scope:** Scan `SKILL.md`, `references/`, `scripts/`, `assets/`.

**Thresholds:**

| Scope | Threshold | Action |
|-------|-----------|--------|
| SKILL.md body (excluding frontmatter) > 500 lines | Recommended | Move sections to `references/` |
| SKILL.md body > 2000 tokens | Mandatory | Extract to `references/` |
| Reference file > 10,000 tokens | Recommended | Split into multiple files |
| Code block in SKILL.md > 30 lines | Candidate | Extract to `scripts/` |
| Code block in SKILL.md > 50 lines | Mandatory | Extract to `scripts/` |

**Target structure:**

```
skill-name/
├── SKILL.md            # <500 lines body, workflow + references index
├── references/         # Detailed docs, loaded on demand
│   ├── {topic}.md      # Each <10,000 tokens, TOC if >100 lines
│   └── ...
├── scripts/            # Extracted code blocks
│   └── {name}.py
└── assets/             # Output templates, unchanged
```

**Protected content in SKILL.md (never extract):**

- Frontmatter (name, description, all metadata)
- Workflow overview (phase list / decision tree)
- References index (which file to load when)
- Dependency / argument declarations

**Extraction targets:**

- Detailed per-phase instructions → `references/{phase-slug}.md`
- Inline code examples > 30 lines → `scripts/{name}.ext`
- Large prompt templates → `references/{template-name}.md`
- Detailed schemas / corpus templates → `references/` (already done correctly)

**Reports:** Write analysis to `docs/CONTEXT_ANALYSIS.md` and migration to `docs/CONTEXT_MIGRATION.md` inside the skill directory (not the project root).

## Deduplication Rules

When the same content appears in multiple files:
1. Keep the authoritative version in the most specific location
2. Replace duplicates with a one-line reference: "See @path/to/authoritative.md"
3. If both locations need the content, extract to a shared fragment

## Precedence Preservation

Claude Code loads configuration in this order (later overrides earlier):
1. Organization-level CLAUDE.md
2. Project-level CLAUDE.md
3. Subdirectory CLAUDE.md files
4. CLAUDE.local.md (user-specific, gitignored)

Never merge content across precedence levels. Fragment within the same level only.
