# Context Analysis — api-doc-scraper Skill

**Generated:** 2026-01-30
**Target:** `C:\Users\vitor\.claude\skills\api-doc-scraper`
**Mode:** Skill

## File Inventory

| File | Lines | Characters | Est. Tokens | Role |
|------|------:|----------:|------------:|------|
| `SKILL.md` (full) | 122 | 4,930 | 1,233 | Skill definition + workflow |
| — frontmatter (lines 1–15) | 15 | 620 | 155 | Trigger metadata |
| — body (lines 16–122) | 107 | 4,310 | 1,078 | Workflow instructions |
| `references/scraping-structure.md` | 88 | 2,830 | 708 | Corpus template + heuristics |
| `scripts/scrape_api_docs.py` | 376 | 12,200 | 3,050 | Python scraper (external) |
| **Total** | **586** | **19,960** | **4,991** | |

## Trigger Cost

The trigger cost is the token budget consumed when the skill activates (SKILL.md body only):

| Metric | Value | Threshold | Status |
|--------|------:|----------:|--------|
| SKILL.md body tokens | 1,078 | < 2,000 (mandatory) | OK |
| SKILL.md body tokens | 1,078 | < 500 (recommended) | OVER |
| SKILL.md body lines | 107 | < 500 (mandatory) | OK |

**Trigger cost: 1,078 tokens** — above the recommended 500-token target but below the mandatory 2,000-token ceiling.

## Fragmentation Candidates

### 1. SKILL.md body — RECOMMENDED extraction (~1,078 tokens → ~400 target)

The SKILL.md body contains four detailed phase descriptions (Discovery, Scraping, Skill Generation, Context Optimization) totaling ~107 lines. The Phase 3 section alone contains a multi-line `/skill-creator` invocation template (~25 lines, ~450 tokens) that could be extracted to a reference file.

**Candidate sections for extraction:**

| Section | Lines | Est. Tokens | Recommendation |
|---------|------:|------------:|----------------|
| Phase 1: Discovery (lines 42–48) | 7 | ~180 | Keep (core workflow) |
| Phase 2: Scraping (lines 50–69) | 20 | ~340 | Extract to reference |
| Phase 3: Skill Generation (lines 72–103) | 32 | ~450 | Extract to reference |
| Phase 4: Context Optimization (lines 105–111) | 7 | ~100 | Keep (short) |

Phases 2 and 3 account for ~790 tokens and contain procedural details + a large template that are only needed during execution, not at trigger time.

### 2. Code blocks in SKILL.md — candidate extraction

| Block | Location | Lines | Recommendation |
|-------|----------|------:|----------------|
| pip install command | Line 24–26 | 3 | Keep (short) |
| Script invocation | Line 54–56 | 3 | Keep (short) |
| `/skill-creator` template | Lines 78–101 | 24 | Extract to `references/skill-creator-template.md` |

The `/skill-creator` invocation template at 24 lines is below the mandatory 50-line extraction threshold but is a self-contained template block that inflates trigger cost. Extracting it would save ~300 tokens from the SKILL.md body.

### 3. No duplicate content detected

No significant content duplication was found between SKILL.md and `references/scraping-structure.md`. The reference file covers corpus format and heuristics, while SKILL.md covers workflow orchestration — clean separation.

### 4. Reference file size — OK

`references/scraping-structure.md` at 708 tokens is well within the 10,000-token threshold. No splitting needed.

### 5. Script file — OK (external)

`scripts/scrape_api_docs.py` at 3,050 tokens runs externally and is never loaded into context. No action needed.

## Top 3 Recommendations

1. **Extract Phase 2 + Phase 3 details to `references/workflow-phases.md`** — Move the detailed scraping instructions and skill-creator template out of SKILL.md, replacing them with one-line summaries. Saves ~790 tokens from trigger cost, bringing SKILL.md body to ~290 tokens (under the 500-token recommended target).

2. **Add a references index to SKILL.md** — The skill currently has no index telling the agent when to load each reference file. Adding a small table (~3 rows) ensures lazy loading.

3. **No further action needed for other files** — The reference file and script are already well-sized and properly separated.

## Projected Savings

| Metric | Before | After (est.) | Change |
|--------|-------:|-------------:|-------:|
| SKILL.md body tokens | 1,078 | ~290 | -73% |
| Trigger cost | 1,078 | ~290 | -73% |
| Total skill tokens | 4,991 | ~4,991 | 0% (content moves, not deleted) |
