---
name: api-doc-scraper
description: >-
  Agentic web scraper that reads API documentation from a URL, extracts endpoints, authentication,
  models, and error handling into a structured corpus, then invokes /skill-creator to generate
  a new skill that serves as an interactive reference for that API. Use when: (1) user provides
  a URL to an API documentation site, (2) user says "scrape api docs", "create api reference skill",
  "import api documentation", "api doc scraper", (3) user wants to create a skill from external
  API documentation for future technical Q&A.
argument-hint: <url> [--name <skill-name>]
allowed-tools: Task, TaskOutput, Bash, Glob, Grep, Read, Edit, Write, WebFetch, WebSearch, AskUserQuestion, Skill
context: fork
agent: general-purpose
dependencies: python>=3.10, requests, beautifulsoup4, lxml
---
# API Documentation Scraper

Scrape web-based API documentation and generate a Claude Code skill that serves as an interactive technical reference for the scraped API.

## Arguments

- `<url>` (required) — Root URL of the API documentation
- `--name <skill-name>` (optional) — Override the generated skill name (default: derived from API name)

## References

| File | Description | Load when |
|------|-------------|-----------|
| `references/workflow-phases.md` | Detailed instructions for all 4 phases (Discovery, Scraping, Skill Generation, Optimization) | Executing any phase |
| `references/scraping-structure.md` | Corpus format template and content extraction heuristics | Building or validating the corpus structure |

## Workflow

The scraper operates in 4 phases:

1. **Discovery** — Fetch root URL, map documentation structure, write `nav-map.json`
2. **Scraping** — Run `scripts/scrape_api_docs.py` to produce `corpus.md` (outside context window)
3. **Skill Generation** — Read `corpus.md`, invoke `/skill-creator` with the content
4. **Context Optimization** — Invoke `/apply-progressive-disclosure optimize` on the output

### Phase 1: Discovery

Fetch the root URL, extract navigation links via `WebFetch`, and write `nav-map.json`. See `references/workflow-phases.md` → Phase 1 for the full WebFetch prompt and steps.

### Phase 2: Scraping (Script-Based)

Run `scripts/scrape_api_docs.py` to fetch all pages and produce `corpus.md`. See `references/workflow-phases.md` → Phase 2 for the full command, script behavior, and error recovery.

### Phase 3: Skill Generation

Derive the skill name, read the corpus, and invoke `/skill-creator` with the structured prompt. See `references/workflow-phases.md` → Phase 3 for the full template and instructions.

### Phase 4: Context Optimization

Run `/apply-progressive-disclosure optimize` on the generated skill and clean up temporary files. See `references/workflow-phases.md` → Phase 4 for details.

## Output

When complete, report to the user:

- Skill name and install path
- Number of endpoints cataloged
- Number of models/schemas captured
- Token budget summary (from progressive disclosure)
- Example invocation: `/{skill-name} "How do I authenticate?"` or similar
