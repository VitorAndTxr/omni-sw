# Early Validation Hooks

Automated validation scripts that detect issues during implementation BEFORE the human review phase. These hooks can be run by the orchestrator or agents to catch problems early.

## Overview

All hooks are standalone Python scripts with no external dependencies (stdlib only). They output JSON to stdout for easy parsing and integration into CI/CD pipelines.

## Available Hooks

### 1. architecture_drift_check.py

Compares the architecture document against the actual implementation to detect drift.

**Usage:**
```bash
python architecture_drift_check.py --architecture <path-to-ARCHITECTURE.md> --src <path-to-src-dir>
```

**What it checks:**
- **Endpoints drift**: Extracts API endpoints from ARCHITECTURE.md and compares against actual route definitions in code
- **Data models drift**: Checks if documented entity/model names exist as classes/interfaces in code
- **Component drift**: Checks if documented service/component names exist as files/classes in code

**Output:**
```json
{
  "status": "drift_detected|aligned|partial",
  "endpoints": {
    "documented": ["GET /api/users", "POST /api/auth/login"],
    "implemented": ["GET /api/users"],
    "missing_in_code": ["POST /api/auth/login"],
    "undocumented_in_arch": []
  },
  "models": {
    "documented": ["User", "Transaction"],
    "found_in_code": ["User"],
    "missing_in_code": ["Transaction"]
  },
  "components": {
    "documented": ["UserService", "AuthController"],
    "found_in_code": ["UserService"],
    "missing_in_code": ["AuthController"]
  },
  "summary": "2 of 4 documented items missing in code"
}
```

**Framework Support:**
- Detects endpoints from Express, Django, Flask, ASP.NET, Spring, and other common frameworks
- Supports patterns: `[HttpGet]`, `[Route]`, `app.get(`, `router.post(`, `@GetMapping`, etc.

---

### 2. convention_checker.py

Validates code against conventions defined in CLAUDE.md.

**Usage:**
```bash
python convention_checker.py --claude-md <path-to-CLAUDE.md> --src <path-to-src-dir>
```

**What it checks:**
- **Forbidden patterns**: Detects any patterns marked as "forbidden" or "do not use" (e.g., `console.log` in production)
- **Naming conventions**: Validates naming patterns (PascalCase, camelCase, snake_case) in source files
- **File structure**: Validates expected directory structure exists
- **Required patterns**: Ensures "always use" or "must use" patterns are present in code

**Output:**
```json
{
  "status": "pass|violations_found",
  "violations": [
    {
      "rule": "Forbidden: console.log in production code",
      "file": "src/services/UserService.ts",
      "line": 42,
      "snippet": "console.log('debug:', user)"
    }
  ],
  "checks_performed": 5,
  "violations_count": 1,
  "summary": "1 violation found across 5 checks"
}
```

**How to define rules in CLAUDE.md:**
Create sections with headers like:
- `## Forbidden Patterns`
- `## Naming Conventions`
- `## File Structure`
- `## Required Patterns`

Each rule should be a bullet point or numbered list item:
```markdown
## Forbidden Patterns
- Do not use `console.log` in production code
- Never use `eval()`
- Forbidden: global variables in modules

## Naming Conventions
- Use camelCase for variables and functions
- Use PascalCase for classes

## File Structure
- All services must be in `/src/services`
- Controllers should be in `/src/controllers`
```

---

### 3. ac_coverage_check.py

Checks if acceptance criteria from backlog stories have representation in the code.

**Usage:**
```bash
python ac_coverage_check.py \
  --backlog-script <path-to-backlog_manager.py> \
  --backlog-path <path-to-backlog.json> \
  --src <path-to-src-dir> \
  [--status "In Review"]
```

**What it checks:**
- Queries stories with the given status (default: "In Review")
- Extracts acceptance criteria (AC) from each story
- Extracts keywords from each AC and searches for them in source code
- Reports which ACs have zero code references (potentially unimplemented)

**Output:**
```json
{
  "status": "all_covered|mostly_covered|gaps_found",
  "stories": [
    {
      "id": "US-001",
      "title": "User login",
      "total_acs": 3,
      "covered_acs": 2,
      "uncovered_acs": [
        {
          "ac": "Given invalid credentials, When user submits login, Then show error message",
          "keywords_searched": ["invalid credentials", "error message", "login"],
          "reason": "No code references found"
        }
      ]
    }
  ],
  "summary": "1 of 3 stories have uncovered acceptance criteria"
}
```

**How it works:**
1. Calls `backlog_manager.py list --status "In Review" --format json` to get stories
2. Falls back to direct JSON parsing if the script isn't available
3. Extracts meaningful keywords from each AC (removes Given/When/Then structure)
4. Searches source files (case-insensitive) for these keywords
5. Reports ACs with no code references as uncovered

**Backlog JSON Format:**
```json
{
  "stories": [
    {
      "id": "US-001",
      "title": "User login",
      "status": "In Review",
      "acceptance_criteria": [
        "Given valid credentials, When user submits login, Then show success",
        "Given invalid credentials, When user submits login, Then show error"
      ]
    }
  ]
}
```

---

## Common Patterns Detected

### architecture_drift_check.py
- **Endpoints**: `GET|POST|PUT|DELETE|PATCH /api/...` patterns in markdown
- **Classes**: `class Name`, `interface Name`, `type Name`, `struct Name`
- **Services**: Files/classes ending with `Service`, `Controller`, `Manager`, `Repository`, etc.

### convention_checker.py
- **Forbidden**: `console.log`, `eval()`, `global variables`, etc.
- **Naming**: camelCase, PascalCase, snake_case validation
- **Structure**: Directory existence checks

### ac_coverage_check.py
- Extracts keywords from AC text (removes stopwords like "the", "and", "user")
- Searches for exact keyword matches with word boundaries
- Case-insensitive search across all source files

---

## Integration

### In CI/CD Pipeline
```bash
# Run all checks
python architecture_drift_check.py --architecture ./ARCHITECTURE.md --src ./src
python convention_checker.py --claude-md ./CLAUDE.md --src ./src
python ac_coverage_check.py --backlog-script ./backlog_manager.py --backlog-path ./backlog.json --src ./src

# Parse JSON output for gate decisions
if [[ $(cat drift_check.json | jq .status) == "drift_detected" ]]; then
  echo "Architecture drift detected - blocking merge"
  exit 1
fi
```

### In Orchestrator
```python
import subprocess
import json

def run_validation_hooks(src_dir, arch_file, claude_file):
    hooks = [
        ['python', 'architecture_drift_check.py', '--architecture', arch_file, '--src', src_dir],
        ['python', 'convention_checker.py', '--claude-md', claude_file, '--src', src_dir],
    ]

    results = {}
    for hook in hooks:
        result = subprocess.run(hook, capture_output=True, text=True)
        results[hook[1]] = json.loads(result.stdout)

    return results
```

---

## Error Handling

All scripts:
- Return error JSON to stderr if files are missing
- Print results to stdout as valid JSON
- Skip binary files and common non-source directories (node_modules, dist, build, etc.)
- Handle encoding errors gracefully with `errors='ignore'`
- Are resilient to regex parsing errors and invalid file formats

## Performance Notes

- Scripts walk entire source trees - performance depends on codebase size
- Typical execution: 1-5 seconds for small-medium projects
- Uses single-threaded walking for consistency
- Early exits when possible (e.g., ac_coverage_check stops searching once all keywords found)

---

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)
- Readable access to architecture files and source code
- Execute permissions on script files (already set)

## Troubleshooting

**No stories found:**
- Check `--status` matches actual story status in backlog.json
- Verify backlog.json path is correct
- Check story JSON format matches expected structure

**Architecture patterns not extracted:**
- Ensure ARCHITECTURE.md uses standard `GET /api/...` format
- Check markdown tables follow standard pipe format
- Verify class names use PascalCase

**Convention rules not detected:**
- CLAUDE.md sections must start with `##` headers
- Rules should be in bullet points (`-`) or numbered lists (`1.`)
- Use backticks for code patterns: `forbidden_pattern`

**Performance issues:**
- Large codebases may take 10+ seconds
- Consider filtering directories or running specific checks only
