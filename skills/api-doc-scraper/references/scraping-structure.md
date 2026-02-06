# Scraping Structure Template

Use this template to organize scraped API documentation into a structured corpus before passing it to `/skill-creator`.

## Corpus Format

```markdown
# {API Name} — Documentation Corpus

## Overview
- **API Name:** {name}
- **Base URL:** {base_url}
- **Version:** {version}
- **Description:** {1-2 sentence summary}

## Authentication
- **Method:** {Bearer token | API key | OAuth 2.0 | etc.}
- **Header:** {Authorization: Bearer <token> | X-API-Key: <key> | etc.}
- **Token acquisition:** {flow description or endpoint}
- **Scopes/permissions:** {if applicable}

## Endpoints

### {Resource Group 1}

#### {METHOD} {path}
- **Description:** {what it does}
- **Parameters:**
  | Name | In | Type | Required | Description |
  |------|----|------|----------|-------------|
  | {name} | {path|query|body|header} | {type} | {yes|no} | {desc} |
- **Request body:** {schema or example}
- **Response:** {status code + schema or example}
- **Errors:** {specific error codes for this endpoint}

### {Resource Group 2}
...

## Models / Schemas

### {ModelName}
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| {field} | {type} | {yes|no} | {desc} |

## Error Handling
- **Error format:** {standard error response shape}
- **Common codes:**
  | Code | Meaning | Resolution |
  |------|---------|------------|
  | {code} | {meaning} | {what to do} |

## Rate Limits & Pagination
- **Rate limit:** {requests per time window}
- **Pagination:** {cursor | offset | page-based}
- **Page size:** {default and max}

## SDK / Client Libraries
- {language}: {package name or link}

## Webhooks (if applicable)
- **Events:** {list of event types}
- **Payload format:** {shape}
- **Signature verification:** {method}
```

## Scraping Priority

When the documentation is too large to scrape exhaustively, prioritize in this order:

1. Authentication (always needed)
2. Endpoint list with method + path + short description
3. Request/response schemas for the most-used endpoints
4. Error codes and formats
5. Rate limits and pagination
6. Webhooks, SDKs, changelog (if relevant)

## Content Extraction Heuristics

When parsing HTML via WebFetch:

- **Navigation links:** Look for sidebar `<nav>`, `<ul>` with links to `/docs/`, `/api/`, `/reference/` paths
- **Endpoint blocks:** Look for HTTP method badges (`GET`, `POST`, etc.) near path patterns
- **Code examples:** Look for `<pre>`, `<code>` blocks, especially those with `curl`, JSON, or language-specific snippets
- **Parameter tables:** Look for `<table>` elements near endpoint descriptions
- **Auth sections:** Search for keywords: "authentication", "authorization", "api key", "bearer", "oauth", "token"
- **Pagination indicators:** Multiple pages often have "next", "previous", page numbers, or section links in the sidebar
