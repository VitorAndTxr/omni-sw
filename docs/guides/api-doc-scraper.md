# api-doc-scraper

Scrapes web-based API documentation from a URL and generates a Claude Code skill that serves as an interactive technical reference for that API. The generated skill can answer questions about endpoints, authentication, models, and error handling without needing to re-fetch the documentation.

## When to use

- Integrating with a third-party API and wanting an always-available reference inside Claude Code
- The API has web documentation but no existing omni-sw skill
- Generating a skill for a team so everyone has access to the same API reference

## Invocation

```
/omni-sw:api-doc-scraper <url>
/omni-sw:api-doc-scraper <url> --name <skill-name>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Root URL of the API documentation site |
| `--name <skill-name>` | No | Override the generated skill name (default: derived from the API name found in the docs) |

## Example

```
/omni-sw:api-doc-scraper https://docs.stripe.com/api
/omni-sw:api-doc-scraper https://api.github.com/docs --name github-api
```

## What it produces

A new Claude Code skill installed at the appropriate skills path, containing:

- Structured endpoint reference with method, path, parameters, and response shapes
- Authentication guide (API keys, OAuth flows, token formats)
- Data model/schema catalog
- Error code reference with descriptions
- Usage examples extracted from the documentation

After generation the skill is automatically optimized for token efficiency via `apply-progressive-disclosure`.

## How it works

The scraper operates in four phases:

1. **Discovery** — Fetches the root URL, maps the documentation navigation structure, and writes an internal `nav-map.json`.

2. **Scraping** — Runs a Python script (`scrape_api_docs.py`) outside the context window to fetch all documentation pages and produce a structured `corpus.md`. This is done out-of-band to avoid filling the context with raw HTML.

3. **Skill generation** — Reads the corpus and invokes `/skill-creator` to produce a well-structured, queryable skill file.

4. **Optimization** — Runs `apply-progressive-disclosure optimize` on the generated skill to minimize its token footprint.

## Dependencies

The scraper requires Python packages for the scraping phase:

```bash
pip install requests beautifulsoup4 lxml
```

## Using the generated skill

Once installed, the skill is invoked by its name and answers questions about the API:

```
/<skill-name> "How do I authenticate with the API?"
/<skill-name> "What fields does the Order object have?"
/<skill-name> "What error code is returned for rate limiting?"
```

## Completion report

When the skill is ready, the scraper reports:

- Skill name and install path
- Number of endpoints cataloged
- Number of models/schemas captured
- Token budget summary after progressive disclosure optimization
- Example invocation command

## Tips

- If the documentation site requires authentication or is behind a login wall, the scraper cannot access it. Use it with publicly accessible documentation only.
- For documentation spread across multiple domains (e.g., a main site and a separate API reference), run the scraper twice and combine manually.
- The `--name` flag is useful when the API name detected from the docs is ambiguous or too long.
- Generated skills can be updated by re-running the scraper against the same URL — it overwrites the previous version.
