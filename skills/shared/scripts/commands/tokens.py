"""
agency_cli tokens — Token analysis, fragmentation, and deduplication.

Usage:
    agency_cli tokens analyze --root <path>                           # Full token analysis
    agency_cli tokens estimate --file <path>                          # Single file token estimate
    agency_cli tokens fragment --file <path> --threshold <n> --output-dir <dir>  # Fragment a file
    agency_cli tokens fragment-skill --file <path> --threshold <n> --output-dir <dir>  # Fragment SKILL.md
    agency_cli tokens deduplicate --root <path>                       # Find duplicates
    agency_cli tokens report --before <json> --after <json> --output <path>  # Before/after report
"""

import argparse
import glob
import json
import math
import os
import re
from collections import defaultdict


def estimate_tokens(text: str) -> int:
    """Estimate token count: ceil(chars / 4)."""
    return math.ceil(len(text) / 4)


def estimate_file_tokens(file_path: str) -> dict:
    """Estimate tokens for a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        chars = len(content)
        lines = content.count('\n') + 1
        tokens = estimate_tokens(content)
        return {
            "file": file_path,
            "chars": chars,
            "lines": lines,
            "tokens": tokens,
        }
    except Exception as e:
        return {"file": file_path, "error": str(e)}


def analyze_project(root: str) -> dict:
    """Full token analysis of a project or skill directory."""
    root = os.path.abspath(root)
    is_skill = os.path.isfile(os.path.join(root, "SKILL.md"))
    is_project = os.path.isfile(os.path.join(root, "CLAUDE.md"))

    files = {}
    total_tokens = 0
    startup_tokens = 0
    candidates = []

    # Patterns to scan
    patterns = []
    if is_project:
        patterns = [
            ("CLAUDE.md", "startup"),
            ("CLAUDE.local.md", "startup"),
            (".claude/settings.json", "startup"),
            (".claude/commands/*.md", "on-demand"),
            (".claude/skills/*/SKILL.md", "on-demand"),
            ("agent_docs/**/*.md", "on-demand"),
            ("docs/**/*.md", "on-demand"),
        ]
    elif is_skill:
        patterns = [
            ("SKILL.md", "trigger"),
            ("references/*.md", "on-demand"),
            ("scripts/*", "never"),
        ]
    else:
        # Scan everything
        patterns = [("**/*.md", "unknown"), ("**/*.json", "unknown")]

    for pattern, load_type in patterns:
        full_pattern = os.path.join(root, pattern)
        for fpath in glob.glob(full_pattern, recursive=True):
            if not os.path.isfile(fpath):
                continue
            info = estimate_file_tokens(fpath)
            if "error" in info:
                continue
            rel_path = os.path.relpath(fpath, root)
            info["relative_path"] = rel_path
            info["load_type"] = load_type
            files[rel_path] = info
            total_tokens += info["tokens"]

            if load_type in ("startup", "trigger"):
                startup_tokens += info["tokens"]

            # Fragmentation candidates
            if info["tokens"] > 500:
                severity = "mandatory" if info["tokens"] > 2000 else "recommended" if info["tokens"] > 1000 else "candidate"
                candidates.append({
                    "file": rel_path,
                    "tokens": info["tokens"],
                    "severity": severity,
                })

    # Sort candidates by token count desc
    candidates.sort(key=lambda c: c["tokens"], reverse=True)

    result = {
        "root": root,
        "type": "skill" if is_skill else "project" if is_project else "generic",
        "files": files,
        "total_tokens": total_tokens,
        "startup_tokens": startup_tokens,
        "on_demand_tokens": total_tokens - startup_tokens,
        "file_count": len(files),
        "fragmentation_candidates": candidates,
    }

    return result


def find_sections(content: str, min_tokens: int = 300) -> list[dict]:
    """Find markdown sections that exceed a token threshold."""
    sections = []
    current_heading = None
    current_content = []
    current_level = 0

    for line in content.split('\n'):
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            # Save previous section
            if current_heading and current_content:
                text = '\n'.join(current_content)
                tokens = estimate_tokens(text)
                if tokens >= min_tokens:
                    slug = re.sub(r'[^a-z0-9]+', '-', current_heading.lower()).strip('-')
                    sections.append({
                        "heading": current_heading,
                        "level": current_level,
                        "slug": slug,
                        "tokens": tokens,
                        "lines": len(current_content),
                        "content": text,
                    })
            current_level = len(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            current_content = [line]
        else:
            current_content.append(line)

    # Last section
    if current_heading and current_content:
        text = '\n'.join(current_content)
        tokens = estimate_tokens(text)
        if tokens >= min_tokens:
            slug = re.sub(r'[^a-z0-9]+', '-', current_heading.lower()).strip('-')
            sections.append({
                "heading": current_heading,
                "level": current_level,
                "slug": slug,
                "tokens": tokens,
                "lines": len(current_content),
                "content": text,
            })

    return sections


def fragment_file(file_path: str, threshold: int, output_dir: str, dry_run: bool = False) -> dict:
    """Fragment a markdown file by extracting sections above threshold."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    before_tokens = estimate_tokens(content)
    sections = find_sections(content, min_tokens=threshold)

    if not sections:
        return {"status": "no_changes", "reason": f"No sections above {threshold} tokens"}

    extracted = []
    remaining = content

    for section in sections:
        # Create output file
        out_path = os.path.join(output_dir, f"{section['slug']}.md")
        if not dry_run:
            os.makedirs(output_dir, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(section["content"])

        # Replace in original with reference
        ref_line = f"See [{section['heading']}]({os.path.relpath(out_path, os.path.dirname(file_path))})"
        remaining = remaining.replace(section["content"], ref_line)

        extracted.append({
            "heading": section["heading"],
            "slug": section["slug"],
            "tokens": section["tokens"],
            "output": out_path,
        })

    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(remaining)

    after_tokens = estimate_tokens(remaining)

    return {
        "status": "dry_run" if dry_run else "applied",
        "file": file_path,
        "before_tokens": before_tokens,
        "after_tokens": after_tokens,
        "savings": before_tokens - after_tokens,
        "extracted_sections": len(extracted),
        "extracted": extracted,
    }


def fragment_skill(skill_path: str, threshold: int, output_dir: str, dry_run: bool = False) -> dict:
    """Fragment a SKILL.md file preserving frontmatter."""
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Separate frontmatter from body
    frontmatter = ""
    body = content
    if content.startswith('---'):
        end_idx = content.index('---', 3)
        frontmatter = content[:end_idx + 3]
        body = content[end_idx + 3:].lstrip('\n')

    before_tokens = estimate_tokens(body)
    sections = find_sections(body, min_tokens=threshold)

    # Protected sections (should not be extracted)
    protected_keywords = ["command routing", "variables", "constraints", "hard constraints", "workflow overview"]

    extracted = []
    remaining_body = body

    for section in sections:
        # Skip protected sections
        if any(kw in section["heading"].lower() for kw in protected_keywords):
            continue

        out_path = os.path.join(output_dir, f"{section['slug']}.md")
        if not dry_run:
            os.makedirs(output_dir, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(section["content"])

        ref_line = f"See [references/{section['slug']}.md](references/{section['slug']}.md)"
        remaining_body = remaining_body.replace(section["content"], ref_line)

        extracted.append({
            "heading": section["heading"],
            "slug": section["slug"],
            "tokens": section["tokens"],
            "output": out_path,
        })

    if not dry_run:
        final = frontmatter + "\n\n" + remaining_body if frontmatter else remaining_body
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write(final)

    after_tokens = estimate_tokens(remaining_body)

    return {
        "status": "dry_run" if dry_run else "applied",
        "file": skill_path,
        "before_tokens": before_tokens,
        "after_tokens": after_tokens,
        "savings": before_tokens - after_tokens,
        "frontmatter_preserved": bool(frontmatter),
        "extracted_sections": len(extracted),
        "extracted": extracted,
    }


def find_duplicates(root: str) -> dict:
    """Find duplicate content across markdown files."""
    root = os.path.abspath(root)
    # Collect all paragraphs from all md files
    paragraphs = defaultdict(list)  # text -> list of (file, line)

    for md_file in glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        rel_path = os.path.relpath(md_file, root)
        # Split into paragraphs (blocks separated by blank lines)
        blocks = re.split(r'\n\s*\n', content)
        for i, block in enumerate(blocks):
            block = block.strip()
            if len(block) > 100:  # Only check substantial blocks
                # Normalize whitespace for comparison
                normalized = re.sub(r'\s+', ' ', block)
                paragraphs[normalized].append({"file": rel_path, "block_index": i})

    # Find duplicates (appear in 2+ files)
    duplicates = []
    for text, locations in paragraphs.items():
        if len(locations) >= 2:
            # Check they're in different files
            unique_files = set(loc["file"] for loc in locations)
            if len(unique_files) >= 2:
                duplicates.append({
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                    "tokens": estimate_tokens(text),
                    "locations": locations,
                    "file_count": len(unique_files),
                })

    duplicates.sort(key=lambda d: d["tokens"], reverse=True)

    return {
        "root": root,
        "duplicates": duplicates,
        "total_duplicate_tokens": sum(d["tokens"] * (d["file_count"] - 1) for d in duplicates),
    }


def generate_report(before_file: str, after_file: str, output_path: str) -> dict:
    """Generate before/after comparison report."""
    with open(before_file, 'r', encoding='utf-8') as f:
        before = json.load(f)
    with open(after_file, 'r', encoding='utf-8') as f:
        after = json.load(f)

    before_total = before.get("total_tokens", 0)
    after_total = after.get("total_tokens", 0)
    before_startup = before.get("startup_tokens", 0)
    after_startup = after.get("startup_tokens", 0)

    reduction_total = before_total - after_total
    reduction_pct = (reduction_total / before_total * 100) if before_total > 0 else 0
    reduction_startup = before_startup - after_startup
    reduction_startup_pct = (reduction_startup / before_startup * 100) if before_startup > 0 else 0

    report_lines = [
        "# Context Optimization Report\n",
        "## Summary\n",
        f"| Metric | Before | After | Reduction |",
        f"|--------|--------|-------|-----------|",
        f"| Total tokens | {before_total:,} | {after_total:,} | {reduction_total:,} ({reduction_pct:.1f}%) |",
        f"| Startup/trigger tokens | {before_startup:,} | {after_startup:,} | {reduction_startup:,} ({reduction_startup_pct:.1f}%) |",
        f"| File count | {before.get('file_count', 0)} | {after.get('file_count', 0)} | — |",
        "",
        "## File Changes\n",
    ]

    # Compare files
    before_files = set(before.get("files", {}).keys())
    after_files = set(after.get("files", {}).keys())

    added = after_files - before_files
    removed = before_files - after_files
    unchanged = before_files & after_files

    if added:
        report_lines.append("### Added Files\n")
        for f in sorted(added):
            info = after["files"][f]
            report_lines.append(f"- `{f}` ({info.get('tokens', 0)} tokens)")
        report_lines.append("")

    if removed:
        report_lines.append("### Removed Files\n")
        for f in sorted(removed):
            info = before["files"][f]
            report_lines.append(f"- `{f}` ({info.get('tokens', 0)} tokens)")
        report_lines.append("")

    modified = []
    for f in sorted(unchanged):
        b_tok = before["files"][f].get("tokens", 0)
        a_tok = after["files"][f].get("tokens", 0)
        if b_tok != a_tok:
            modified.append({"file": f, "before": b_tok, "after": a_tok, "diff": a_tok - b_tok})

    if modified:
        report_lines.append("### Modified Files\n")
        report_lines.append("| File | Before | After | Change |")
        report_lines.append("|------|--------|-------|--------|")
        for m in modified:
            sign = "+" if m["diff"] > 0 else ""
            report_lines.append(f"| `{m['file']}` | {m['before']} | {m['after']} | {sign}{m['diff']} |")
        report_lines.append("")

    report_content = "\n".join(report_lines)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return {
        "output": output_path,
        "total_reduction": reduction_total,
        "total_reduction_pct": round(reduction_pct, 1),
        "startup_reduction": reduction_startup,
        "startup_reduction_pct": round(reduction_startup_pct, 1),
    }


def handle_tokens(args: list[str]) -> dict:
    if not args:
        raise ValueError("Subcommand required: analyze, estimate, fragment, fragment-skill, deduplicate, report")

    subcmd = args[0]

    if subcmd == "analyze":
        parser = argparse.ArgumentParser(prog="agency_cli tokens analyze")
        parser.add_argument("--root", required=True)
        opts = parser.parse_args(args[1:])
        return analyze_project(opts.root)

    elif subcmd == "estimate":
        parser = argparse.ArgumentParser(prog="agency_cli tokens estimate")
        parser.add_argument("--file", required=True)
        opts = parser.parse_args(args[1:])
        return estimate_file_tokens(opts.file)

    elif subcmd == "fragment":
        parser = argparse.ArgumentParser(prog="agency_cli tokens fragment")
        parser.add_argument("--file", required=True)
        parser.add_argument("--threshold", type=int, default=300)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--dry-run", action="store_true")
        opts = parser.parse_args(args[1:])
        return fragment_file(opts.file, opts.threshold, opts.output_dir, opts.dry_run)

    elif subcmd == "fragment-skill":
        parser = argparse.ArgumentParser(prog="agency_cli tokens fragment-skill")
        parser.add_argument("--file", required=True)
        parser.add_argument("--threshold", type=int, default=300)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--dry-run", action="store_true")
        opts = parser.parse_args(args[1:])
        return fragment_skill(opts.file, opts.threshold, opts.output_dir, opts.dry_run)

    elif subcmd == "deduplicate":
        parser = argparse.ArgumentParser(prog="agency_cli tokens deduplicate")
        parser.add_argument("--root", required=True)
        opts = parser.parse_args(args[1:])
        return find_duplicates(opts.root)

    elif subcmd == "report":
        parser = argparse.ArgumentParser(prog="agency_cli tokens report")
        parser.add_argument("--before", required=True)
        parser.add_argument("--after", required=True)
        parser.add_argument("--output", required=True)
        opts = parser.parse_args(args[1:])
        return generate_report(opts.before, opts.after, opts.output)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}")
