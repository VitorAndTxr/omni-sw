# Extending the Agency

How to add new agents, phases, artifacts, and utility skills.

## Adding a New Agent

1. **Create the skill file:** Add `~/.claude/skills/<agent-name>/SKILL.md` following the existing pattern:
   - YAML frontmatter with `name` and `description` (include trigger phrases).
   - `# <Agent Name> Agent` heading.
   - Identity & Position section (role, hierarchy, client interaction, hard constraints).
   - Project Root Resolution section (copy from existing agent, adjust example paths).
   - Phase Routing section.
   - One section per phase mode the agent participates in, each with: role in phase (LEADS/ASSISTS), workflow steps, output artifacts, allowed tools, input artifacts.

2. **Update the hierarchy:** Define who the new agent reports to and who it reviews/manages. Update existing agents' Identity sections if the hierarchy changes.

3. **Update CLAUDE.md:** Add an entry in the Agent Overrides section for project-specific adjustments.

4. **Update README_AGENCY.md:** Add the agent to the Role-Phase Matrix, Agent Reference index, and File Index.

5. **Update USAGE_GUIDE.md:** Add the agent's commands to each phase where it participates.

## Adding a New Phase

1. **Define the phase:** Determine its position in the sequence, purpose, inputs, outputs, and gate conditions.

2. **Update skill files:** For each agent that participates, add a new Phase section in their `SKILL.md` with the full workflow, role, tools, and artifacts.

3. **Create a template (if the phase produces a document):** Add `~/.claude/docs/templates/<ARTIFACT>.md` with the structure agents should follow.

4. **Update feedback loops:** If the phase has a gate, define where failure routes back to.

5. **Update README_AGENCY.md and USAGE_GUIDE.md.**

## Adding a New Artifact

1. **Create the template:** Add `~/.claude/docs/templates/<ARTIFACT>.md` with section headings, placeholder tables, and guidance.

2. **Update the producing agent's skill file:** Add the artifact to the relevant phase mode's workflow and output list.

3. **Update the Artifact Map** in `~/.claude/docs/agency/artifact-map.md` and `USAGE_GUIDE.md`.

## Utility Skills

In addition to role-based agents, the agency includes standalone utility skills that any user can invoke directly. These are not phase-bound agents -- they perform specific cross-cutting tasks.

| Skill | Command | Purpose |
|-------|---------|---------|
| Progressive Disclosure Optimizer | `/apply-progressive-disclosure` | Analyze and restructure Claude Code config files for token efficiency |
| Project Map | `/project-map` | Discover and map all repositories in a multi-repo project, producing consolidated documentation |
| API Doc Scraper | `/api-doc-scraper` | Scrape web API docs from a URL, generate an interactive reference skill via /skill-creator |

Utility skills live in `~/.claude/skills/` alongside agent skills but follow a simpler structure: command routing (not phase routing), no identity/hierarchy, and no artifact production within the SDLC phases. They can be invoked at any point in the workflow.

## Key Modification Points

| What to change | Files to edit |
|----------------|--------------|
| Agent behavior | `~/.claude/skills/<agent>/SKILL.md` |
| Project conventions | `CLAUDE.md` (Agent Overrides, Conventions, Forbidden Patterns) |
| Automated guardrails | `.claude/hooks.json` (project-level) |
| Artifact structure | `~/.claude/docs/templates/<artifact>.md` |
| Usage instructions | `~/.claude/docs/USAGE_GUIDE.md` |
| Hand-off reference | `~/.claude/README_AGENCY.md` (hub) |

## Conventions to Follow

- Skill files use the same internal structure: frontmatter, identity, project root resolution, phase routing, then phase sections.
- Phase sections always include: role in phase, workflow steps (numbered), output artifacts, allowed tools, input artifacts.
- Templates use placeholder text in italics (`*placeholder*`) and include the phase/owner in a blockquote at the top.
- Agents always read `CLAUDE.md` as their first or second workflow step.
- Artifact paths are relative to the project root (where `CLAUDE.md` lives), not the agency root.
