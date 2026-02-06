# Task Agent Prompt Template

Substitute `{{REPO_PATH}}` and `{{REPO_NAME}}` before sending to each Task agent.

## Prompt

```
Map the repository "{{REPO_NAME}}" at "{{REPO_PATH}}" and produce a structured JSON summary.

## Step 1: Invoke /repo-map

Call the Skill tool with skill: "repo-map" and args: "{{REPO_PATH}}".

Wait for it to complete. This runs the full repo-map workflow: discovery, analysis, database diagrams, endpoint catalog, workflow diagrams, supplementary diagrams, CLAUDE.md, and progressive disclosure optimization.

## Step 2: Produce JSON Summary

After /repo-map completes, read the generated artifacts (CLAUDE.md and docs/) at "{{REPO_PATH}}" and write a structured JSON file to "{{REPO_PATH}}/docs/_repo-map-summary.json".

The JSON MUST follow this exact schema:

{
  "name": "{{REPO_NAME}}",
  "path": "{{REPO_PATH}}",
  "stack": {
    "runtime": "",
    "framework": "",
    "orm": "",
    "database": "",
    "language": "",
    "infrastructure": []
  },
  "entryPoints": ["relative/path/to/entry"],
  "databases": [
    {
      "name": "database_name",
      "engine": "PostgreSQL|MySQL|SQLite|MSSQL|MongoDB|etc",
      "connectionKey": "env var or config key",
      "entities": ["EntityA", "EntityB"]
    }
  ],
  "endpoints": [
    {
      "method": "GET|POST|PUT|DELETE|PATCH",
      "route": "/api/resource",
      "controller": "ResourceController",
      "auth": true,
      "description": "Brief description"
    }
  ],
  "integrations": [
    {
      "type": "http|grpc|rabbitmq|kafka|servicebus|redis|etc",
      "target": "service name or URL",
      "baseUrl": "http://service:port",
      "description": "Brief description"
    }
  ],
  "envVars": [
    {
      "name": "VAR_NAME",
      "usedBy": "component or project",
      "purpose": "Brief description"
    }
  ],
  "conventions": ["PascalCase classes", "kebab-case endpoints"],
  "domainTerms": [
    {
      "term": "Term",
      "definition": "Definition",
      "source": "file or component"
    }
  ],
  "errors": []
}

Rules:
- Populate every field from the generated CLAUDE.md and docs/ artifacts.
- Use empty arrays for sections with no data (e.g., a frontend with no databases).
- The "errors" array captures any issues encountered during mapping. Leave empty if none.
- All paths in "entryPoints" are relative to the repository root.
- Do NOT include connection string passwords in "connectionKey" — use the config key name only.
```
