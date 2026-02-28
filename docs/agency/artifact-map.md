# Artifact Map

Directory structure showing all artifacts produced during the SDLC workflow and the agency's own file layout.

## Project Artifacts (per-project)

```mermaid
graph TD
    Root["project-root/"]
    Root --> CLAUDE["CLAUDE.md<br/><i>Project config — all agents read</i>"]
    Root --> README["README.md<br/><i>Phase 7 — PM leads</i>"]
    Root --> CHANGELOG["CHANGELOG.md<br/><i>Phase 7 — PM leads</i>"]
    Root --> src["src/<br/><i>Phase 4 — Dev leads</i>"]
    src --> Api & Application & Domain & Infrastructure
    Root --> tests["tests/<br/><i>Phase 6 — QA leads</i>"]
    tests --> Unit & Integration
    Root --> docs["docs/"]
    docs --> BRIEF["PROJECT_BRIEF.md<br/><i>Phase 1 — PM leads</i>"]
    docs --> BACKLOG["BACKLOG.md<br/><i>Phase 1 — PO produces</i>"]
    docs --> ARCH["ARCHITECTURE.md<br/><i>Phase 2 — TL leads</i>"]
    docs --> VALID["VALIDATION.md<br/><i>Phase 3 — PM + TL + PO</i>"]
    docs --> REVIEW["REVIEW.md<br/><i>Phase 5 — TL + QA</i>"]
    docs --> TEST["TEST_REPORT.md<br/><i>Phase 6 — QA leads</i>"]
    docs --> APIREF["API_REFERENCE.md<br/><i>Phase 7 — TL leads</i>"]
```

## Agency Files (shared across all projects)

```mermaid
graph TD
    Root["~/.claude/ <i>(agency root)</i>"]
    Root --> CMD["CLAUDE.md<br/><i>User's global instructions</i>"]
    Root --> AGENCY["README_AGENCY.md<br/><i>Agency hand-off hub</i>"]
    Root --> skills["skills/"]
    skills --> pm["pm/SKILL.md"] & po["po/SKILL.md"] & tl["tl/SKILL.md"] & dev["dev/SKILL.md"] & qa["qa/SKILL.md"]
    skills --> apd["apply-progressive-disclosure/"]
    apd --> apdSkill["SKILL.md"] & apdRefs["references/<br/>fragmentation-rules.md<br/>report-format.md"]
    skills --> pmap["project-map/"]
    pmap --> pmapSkill["SKILL.md"] & pmapRefs["references/<br/>project-claude-md-template.md<br/>task-agent-prompt-template.md"]
    skills --> rmap["repo-map/"]
    rmap --> rmapSkill["SKILL.md"] & rmapRefs["references/<br/>claude-md-template.md<br/>database-template.md<br/>endpoints-template.md<br/>workflows-template.md"]
    Root --> docsDir["docs/"]
    docsDir --> UG["USAGE_GUIDE.md"]
    docsDir --> agencyDir["agency/<br/><i>Extracted reference docs</i>"]
    docsDir --> templates["templates/<br/>CLAUDE_TEMPLATE.md<br/>PROJECT_BRIEF.md<br/>BACKLOG.md<br/>ARCHITECTURE.md<br/>VALIDATION.md<br/>REVIEW.md<br/>TEST_REPORT.md<br/>API_REFERENCE.md"]
```

Hooks are project-level and live in each project's `.claude/hooks.json`.
