# Artifact Map

Directory structure showing all artifacts produced during the SDLC workflow and the agency's own file layout.

## Project Artifacts (per-project)

```
project-root/                            (per-project, contains CLAUDE.md)
├── CLAUDE.md                            # Project config — all agents read this
├── README.md                            # Phase 7 — PM leads
├── CHANGELOG.md                         # Phase 7 — PM leads
├── src/                                 # Phase 4 — Dev leads
│   ├── Api/
│   ├── Application/
│   ├── Domain/
│   └── Infrastructure/
├── tests/                               # Phase 6 — QA leads
│   ├── Unit/
│   └── Integration/
└── docs/
    ├── PROJECT_BRIEF.md                 # Phase 1 — PM leads
    ├── BACKLOG.md                       # Phase 1 — PO produces
    ├── ARCHITECTURE.md                  # Phase 2 — TL leads (updated Phase 7)
    ├── VALIDATION.md                    # Phase 3 — PM (biz) + TL (tech) + PO
    ├── REVIEW.md                        # Phase 5 — TL leads + QA assists
    ├── TEST_REPORT.md                   # Phase 6 — QA leads
    └── API_REFERENCE.md                 # Phase 7 — TL leads
```

## Agency Files (shared across all projects)

```
~/.claude/                               (agency root)
├── CLAUDE.md                            # User's global Claude instructions
├── README_AGENCY.md                     # Agency hand-off hub document
├── skills/
│   ├── pm/SKILL.md                      # PM agent definition
│   ├── po/SKILL.md                      # PO agent definition
│   ├── tl/SKILL.md                      # TL agent definition
│   ├── dev/SKILL.md                     # Dev agent definition
│   ├── qa/SKILL.md                      # QA agent definition
│   ├── apply-progressive-disclosure/    # Context optimization utility
│   │   ├── SKILL.md                     # Skill entry point
│   │   └── references/
│   │       ├── fragmentation-rules.md   # Thresholds and rules
│   │       └── report-format.md         # Output report templates
│   ├── project-map/                     # Multi-repo mapping orchestrator
│   │   ├── SKILL.md                     # Skill entry point
│   │   └── references/
│   │       ├── project-claude-md-template.md
│   │       └── task-agent-prompt-template.md
│   └── repo-map/                        # Repository discovery & mapping
│       ├── SKILL.md                     # Skill entry point
│       └── references/
│           ├── claude-md-template.md
│           ├── database-template.md
│           ├── endpoints-template.md
│           └── workflows-template.md
└── docs/
    ├── USAGE_GUIDE.md                   # Quick-start usage guide
    ├── agency/                          # Extracted reference docs (this directory)
    └── templates/
        ├── CLAUDE_TEMPLATE.md           # Project configuration template
        ├── PROJECT_BRIEF.md             # Template for Phase 1 brief
        ├── BACKLOG.md                   # Template for Phase 1 backlog
        ├── ARCHITECTURE.md              # Template for Phase 2 architecture
        ├── VALIDATION.md                # Template for Phase 3 validation gate
        ├── REVIEW.md                    # Template for Phase 5 code review
        ├── TEST_REPORT.md              # Template for Phase 6 test report
        └── API_REFERENCE.md             # Template for Phase 7 API docs
```

Hooks are project-level and live in each project's `.claude/hooks.json`.
