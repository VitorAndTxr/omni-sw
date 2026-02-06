#!/usr/bin/env python3
"""
API Documentation Scraper

Fetches API documentation pages from a navigation map and produces a structured
Markdown corpus file. Runs outside the LLM context window to save tokens.

Usage:
    python scrape_api_docs.py <nav-map.json> --output <corpus.md> [--timeout 15] [--max-pages 50]

nav-map.json format:
    [
        {"title": "Authentication", "url": "https://docs.example.com/auth", "category": "auth"},
        {"title": "List Users", "url": "https://docs.example.com/api/users", "category": "endpoints"},
        ...
    ]

Valid categories: overview, auth, endpoints, models, errors, rate-limits, webhooks, sdks, changelog, other
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print(
        "ERROR: Missing dependencies. Install them with:\n"
        "  pip install requests beautifulsoup4 lxml\n",
        file=sys.stderr,
    )
    sys.exit(1)

CATEGORY_PRIORITY = [
    "overview",
    "auth",
    "endpoints",
    "models",
    "errors",
    "rate-limits",
    "webhooks",
    "sdks",
    "changelog",
    "other",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; APIDocScraper/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ---------------------------------------------------------------------------
# HTML extraction helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Collapse whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def extract_code_blocks(soup: BeautifulSoup) -> list[str]:
    """Extract all <pre> and <code> blocks as fenced markdown."""
    blocks = []
    for el in soup.select("pre, pre code"):
        code = el.get_text(separator="\n").strip()
        if not code:
            continue
        lang = ""
        classes = el.get("class", [])
        for cls in classes:
            if isinstance(cls, str):
                match = re.search(r"language-(\w+)", cls)
                if match:
                    lang = match.group(1)
                    break
        blocks.append(f"```{lang}\n{code}\n```")
    return blocks


def extract_tables(soup: BeautifulSoup) -> list[str]:
    """Convert HTML tables to Markdown tables."""
    tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        md_rows = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [clean_text(c.get_text()) for c in cells]
            md_rows.append("| " + " | ".join(cell_texts) + " |")
            if i == 0:
                md_rows.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
        tables.append("\n".join(md_rows))
    return tables


def extract_headings(soup: BeautifulSoup) -> list[tuple[int, str]]:
    """Return list of (level, text) for h1-h6."""
    headings = []
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(tag.name[1])
        headings.append((level, clean_text(tag.get_text())))
    return headings


def extract_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Try to isolate the main documentation content area."""
    # Common doc site content selectors
    selectors = [
        "main",
        "[role='main']",
        ".main-content",
        ".content",
        ".documentation",
        ".doc-content",
        ".markdown-body",
        "article",
        "#content",
        "#main-content",
        ".api-content",
        ".page-content",
    ]
    for sel in selectors:
        found = soup.select_one(sel)
        if found and len(found.get_text(strip=True)) > 100:
            return BeautifulSoup(str(found), "lxml")
    return soup


def html_to_markdown(soup: BeautifulSoup) -> str:
    """Best-effort HTML to Markdown conversion for doc content."""
    content = extract_main_content(soup)

    # Remove nav, header, footer, sidebar, scripts, styles
    for tag in content.find_all(["nav", "header", "footer", "script", "style", "aside"]):
        tag.decompose()

    parts = []

    for el in content.descendants:
        if not isinstance(el, Tag):
            continue

        if re.match(r"^h[1-6]$", el.name):
            level = int(el.name[1])
            text = clean_text(el.get_text())
            if text:
                parts.append(f"\n{'#' * level} {text}\n")

        elif el.name == "p":
            text = clean_text(el.get_text())
            if text and len(text) > 5:
                parts.append(f"\n{text}\n")

        elif el.name == "pre":
            code = el.get_text(separator="\n").strip()
            if code:
                lang = ""
                code_el = el.find("code")
                check_el = code_el if code_el else el
                for cls in check_el.get("class", []):
                    if isinstance(cls, str):
                        match = re.search(r"language-(\w+)", cls)
                        if match:
                            lang = match.group(1)
                            break
                parts.append(f"\n```{lang}\n{code}\n```\n")

        elif el.name == "table":
            rows = el.find_all("tr")
            if rows:
                md_rows = []
                for i, row in enumerate(rows):
                    cells = row.find_all(["th", "td"])
                    cell_texts = [clean_text(c.get_text()) for c in cells]
                    md_rows.append("| " + " | ".join(cell_texts) + " |")
                    if i == 0:
                        md_rows.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
                parts.append("\n" + "\n".join(md_rows) + "\n")

        elif el.name in ("ul", "ol"):
            # Only process top-level lists (not nested)
            if el.parent and el.parent.name not in ("li",):
                for li in el.find_all("li", recursive=False):
                    text = clean_text(li.get_text())
                    if text:
                        prefix = "-" if el.name == "ul" else "1."
                        parts.append(f"  {prefix} {text}")

    # Deduplicate consecutive identical lines
    result = "\n".join(parts)
    lines = result.split("\n")
    deduped = []
    prev = None
    for line in lines:
        if line != prev or line.strip() == "":
            deduped.append(line)
        prev = line
    return "\n".join(deduped)


# ---------------------------------------------------------------------------
# Category-specific extraction
# ---------------------------------------------------------------------------

def extract_content(soup: BeautifulSoup, url: str, title: str, category: str) -> str:
    """Extract page content with a category-appropriate heading."""
    md = html_to_markdown(soup)
    heading_map = {
        "auth": "Authentication",
        "errors": "Error Handling",
        "rate-limits": "Rate Limits & Pagination",
        "webhooks": "Webhooks",
        "sdks": "SDK / Client Libraries",
        "changelog": "Changelog",
    }
    heading = heading_map.get(category) or title or category.replace("-", " ").title()
    return f"### {heading}\n\n_Source: {url}_\n\n{md}"


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 15) -> BeautifulSoup | None:
    """Fetch a URL and return parsed BeautifulSoup, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  WARN: Failed to fetch {url}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Corpus assembly
# ---------------------------------------------------------------------------

def build_corpus(nav_map: list[dict], timeout: int, max_pages: int) -> str:
    """Fetch all pages and assemble into a structured Markdown corpus."""
    # Sort by category priority
    priority = {cat: i for i, cat in enumerate(CATEGORY_PRIORITY)}
    sorted_entries = sorted(nav_map, key=lambda e: priority.get(e.get("category", "other"), 99))

    # Limit page count
    if len(sorted_entries) > max_pages:
        print(
            f"  INFO: Limiting to {max_pages} pages (from {len(sorted_entries)} total). "
            f"Prioritizing by category order.",
            file=sys.stderr,
        )
        sorted_entries = sorted_entries[:max_pages]

    sections: dict[str, list[str]] = {}
    stats = {"total": len(sorted_entries), "fetched": 0, "failed": 0}

    for i, entry in enumerate(sorted_entries, 1):
        url = entry["url"]
        title = entry.get("title", "")
        category = entry.get("category", "other")

        print(f"  [{i}/{stats['total']}] Fetching: {title or url} ({category})", file=sys.stderr)

        soup = fetch_page(url, timeout)
        if not soup:
            stats["failed"] += 1
            continue
        stats["fetched"] += 1

        content = extract_content(soup, url, title, category)

        if category not in sections:
            sections[category] = []
        sections[category].append(content)

        # Polite delay between requests
        if i < stats["total"]:
            time.sleep(0.5)

    # Assemble corpus
    corpus_parts = []
    corpus_parts.append("# API Documentation Corpus\n")
    corpus_parts.append(
        f"_Scraped {stats['fetched']} of {stats['total']} pages "
        f"({stats['failed']} failed)_\n"
    )

    # Emit sections in priority order
    section_headings = {
        "overview": "Overview",
        "auth": "Authentication",
        "endpoints": "Endpoints",
        "models": "Models / Schemas",
        "errors": "Error Handling",
        "rate-limits": "Rate Limits & Pagination",
        "webhooks": "Webhooks",
        "sdks": "SDK / Client Libraries",
        "changelog": "Changelog",
        "other": "Additional Documentation",
    }

    for cat in CATEGORY_PRIORITY:
        if cat in sections:
            heading = section_headings.get(cat, cat.title())
            corpus_parts.append(f"\n## {heading}\n")
            corpus_parts.extend(sections[cat])

    return "\n".join(corpus_parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape API docs from a navigation map and produce a Markdown corpus."
    )
    parser.add_argument("nav_map", help="Path to nav-map.json file")
    parser.add_argument("--output", "-o", required=True, help="Output corpus Markdown file path")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP request timeout in seconds (default: 15)")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to fetch (default: 50)")
    args = parser.parse_args()

    nav_map_path = Path(args.nav_map)
    if not nav_map_path.exists():
        print(f"ERROR: Navigation map not found: {nav_map_path}", file=sys.stderr)
        sys.exit(1)

    with open(nav_map_path, "r", encoding="utf-8") as f:
        nav_map = json.load(f)

    if not isinstance(nav_map, list) or len(nav_map) == 0:
        print("ERROR: nav-map.json must be a non-empty array of objects.", file=sys.stderr)
        sys.exit(1)

    # Validate entries
    for i, entry in enumerate(nav_map):
        if "url" not in entry:
            print(f"ERROR: Entry {i} missing 'url' field.", file=sys.stderr)
            sys.exit(1)
        if "category" not in entry:
            entry["category"] = "other"
        if "title" not in entry:
            entry["title"] = ""

    print(f"Scraping {len(nav_map)} pages...", file=sys.stderr)
    corpus = build_corpus(nav_map, args.timeout, args.max_pages)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(corpus)

    # Print stats to stdout for Claude to capture
    line_count = corpus.count("\n") + 1
    char_count = len(corpus)
    token_estimate = -(-char_count // 4)  # ceil division
    print(f"Corpus written to: {output_path}")
    print(f"  Lines: {line_count}")
    print(f"  Characters: {char_count}")
    print(f"  Estimated tokens: {token_estimate}")


if __name__ == "__main__":
    main()
