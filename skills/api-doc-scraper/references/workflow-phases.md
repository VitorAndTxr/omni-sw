# Workflow Phase Details

Detailed instructions for all workflow phases. Load this file when executing any phase.

## Phase 1: Discovery

1. Parse the argument to extract the URL. If `--name` is provided, store it for Phase 3.
2. Create a temporary working directory: `$TEMP/api-doc-scraper-{timestamp}/`
3. Use `WebFetch` on the root URL with prompt: "Extract all navigation links, sidebar entries, and section headings that point to API documentation pages. For each link return: page title, full URL, and category. Valid categories: overview, auth, endpoints, models, errors, rate-limits, webhooks, sdks, changelog. Ignore links to blog posts, marketing pages, or non-documentation content. Return as a JSON array of objects with keys: title, url, category."
4. Parse the response into a JSON array. Resolve relative URLs to absolute. Write the result to `nav-map.json` in the working directory.
5. If the navigation map has more than 30 entries, ask the user which categories to prioritize using `AskUserQuestion`. Default priority order: overview > auth > endpoints > models > errors > rate-limits > webhooks > sdks > changelog.

## Phase 2: Scraping (Script-Based)

Run the scraping script to fetch all pages and produce the corpus. This executes entirely outside the context window, saving tokens proportional to the number of documentation pages.

```bash
python scripts/scrape_api_docs.py nav-map.json --output corpus.md --max-pages 50 --timeout 15
```

The script:
- Fetches each URL in category-priority order
- Extracts main content area (strips nav, header, footer, sidebar)
- Converts HTML to Markdown (headings, tables, code blocks, lists)
- Assembles a structured corpus grouped by category
- Prints stats (lines, characters, estimated tokens) to stdout

If the script fails due to missing dependencies, install them:
```bash
pip install requests beautifulsoup4 lxml
```

After the script completes, read only the **first 50 lines** of `corpus.md` to extract the API name and verify the corpus structure. Do NOT read the entire file into context.

## Phase 3: Skill Generation

1. Derive the skill name: use `--name` if provided, otherwise slugify the API name from the corpus header (e.g., "Stripe API" → `stripe-api-reference`).
2. Read `corpus.md` in full (this is the one context-loading step — unavoidable since `/skill-creator` needs the content).
3. Invoke `/skill-creator` with this argument:

```
/skill-creator Create a skill named "{api-name}-api-reference" with the following specification:

PURPOSE: Interactive technical reference for the {API Name} API. Enables answering questions about endpoints, authentication, request/response schemas, error handling, and usage patterns.

DESCRIPTION (for frontmatter): "{API Name} API technical reference — interactive documentation for endpoints, authentication, models, error codes, and usage patterns. Use when: (1) building integrations with {API Name}, (2) querying {API Name} endpoints, (3) debugging {API Name} API errors, (4) user mentions '{API Name}', '{api-name} api', '{api-name} integration'."

STRUCTURE:
- SKILL.md: Overview (API name, base URL, auth summary), quick-start example, endpoint index table, and references index
- references/authentication.md: Full auth details, token flows, examples
- references/endpoints.md: Complete endpoint catalog grouped by resource
- references/models.md: All data models/schemas
- references/errors.md: Error codes, formats, troubleshooting
- Additional references/ files if the corpus contains webhooks, SDKs, or rate-limit details

CONVENTIONS (from README_AGENCY.md at D:\Repos\README_AGENCY.md):
- Follow the agency's skill structure: SKILL.md + references/ + optional scripts/ and assets/
- Progressive disclosure: SKILL.md stays under 500 lines; detailed content goes in references/
- Reference files include a table of contents if >100 lines
- Frontmatter description includes both "what" and "when to use" triggers

CORPUS:
{full contents of corpus.md}
```

Let `/skill-creator` handle all file creation (SKILL.md, references/, frontmatter). Do not manually write skill files.

## Phase 4: Context Optimization

After `/skill-creator` completes:

1. Invoke `/apply-progressive-disclosure optimize` targeting the generated skill's directory.
2. This ensures reference files respect token budgets and fragments any oversized documents.
3. Clean up temporary files (`nav-map.json`, `corpus.md`) from the working directory.
