# Report Format

## Analysis Report Structure

Use this exact structure for the analysis report output:

```markdown
# Progressive Disclosure Analysis

**Repository:** {repo_path}
**Scanned at:** {date}
**Total configuration tokens:** {total_tokens}

## Token Budget Summary

| File | Tokens | % of Total | Status |
|------|--------|-----------|--------|
| CLAUDE.md | X | Y% | OVER / OK |
| ... | ... | ... | ... |
| **Total** | **X** | **100%** | |

## Startup Cost

Tokens loaded on every session start (CLAUDE.md + always-loaded files): **{startup_tokens}**

## Fragmentation Candidates

### Priority 1: Mandatory (>2000 tokens)
| File | Tokens | Sections to extract |
|------|--------|-------------------|
| ... | ... | ... |

### Priority 2: Recommended (>1000 tokens)
| File | Tokens | Sections to extract |
|------|--------|-------------------|
| ... | ... | ... |

### Priority 3: Candidate (>500 tokens)
| File | Tokens | Sections to extract |
|------|--------|-------------------|
| ... | ... | ... |

## Duplicate Content

| Content | Found in | Recommendation |
|---------|----------|---------------|
| ... | file1, file2 | Keep in file1, reference from file2 |

## Projected Savings

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Startup tokens | X | Y | Z% |
| Total config tokens | X | Y | Z% |
| Files loaded at startup | X | Y | -N |
```

## Migration Report Structure

Use after applying optimizations:

```markdown
# Progressive Disclosure Migration Report

**Applied at:** {date}

## Changes Made

| Action | Source | Destination | Tokens moved |
|--------|--------|-------------|-------------|
| Extract section | CLAUDE.md#Architecture | agent_docs/architecture.md | 450 |
| Convert to skill | CLAUDE.md#Deploy Guide | .claude/commands/deploy.md | 300 |
| Extract script | CLAUDE.md#validate | scripts/validate.py | 200 |
| Deduplicate | file1.md, file2.md | Kept in file1.md | 150 |

## Token Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| CLAUDE.md tokens | X | Y | -Z% |
| Startup cost | X | Y | -Z% |
| Total accessible tokens | X | X | 0% (preserved) |

## New File Structure

(tree output of created/modified files)

## Verification Checklist

- [ ] All original content accessible via index or skill
- [ ] No broken @references
- [ ] CLAUDE.md < 500 tokens
- [ ] Index table covers all extracted docs
- [ ] Precedence hierarchy preserved
```
