#!/usr/bin/env python3
"""
Acceptance Criteria Coverage Check

Checks if acceptance criteria from backlog stories have representation in code.

Usage:
    python ac_coverage_check.py --backlog-script <path-to-backlog_manager.py> --backlog-path <path-to-backlog.json> --src <path-to-src-dir> [--status "In Review"]

Checks:
    - Queries stories with the given status (default: "In Review")
    - For each story, gets acceptance criteria
    - For each AC, extracts keywords/entities and searches for them in source code
    - Reports which ACs have zero code references (potentially unimplemented)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def extract_keywords_from_ac(ac_text):
    """
    Extract meaningful keywords from acceptance criteria.
    Removes Given/When/Then connectors and extracts entities.
    """
    # Remove Given/When/Then structure
    text = re.sub(r'\b(Given|When|Then|And|But)\b', '', ac_text, flags=re.IGNORECASE)

    # Extract quoted strings (likely entities or values)
    quoted = re.findall(r'["\']([^"\']+)["\']', text)

    # Extract capitalized words (likely class/method names)
    capitalized = re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', text)

    # Extract lowercase words that might be method/variable names
    lowercase = re.findall(r'\b([a-z][a-z0-9_]*)\b', text)

    # Filter out common stop words
    stop_words = {'the', 'and', 'or', 'not', 'is', 'are', 'be', 'have', 'has', 'do', 'does', 'can', 'should', 'will', 'would', 'user', 'users', 'show', 'display', 'return', 'submit', 'click', 'enter', 'type', 'see', 'view'}

    all_keywords = quoted + capitalized + [k for k in lowercase if k not in stop_words]

    # Remove duplicates while preserving order
    keywords = []
    seen = set()
    for k in all_keywords:
        if k.lower() not in seen:
            keywords.append(k)
            seen.add(k.lower())

    return keywords


def get_stories_from_backlog(backlog_script, backlog_path, status):
    """
    Query stories from backlog using backlog_manager.py.
    Falls back to direct JSON parsing if script execution fails.
    """
    stories = []

    # Try using the backlog_manager.py script
    if os.path.exists(backlog_script):
        try:
            result = subprocess.run(
                ['python3', backlog_script, 'list', '--status', status, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'stories' in data:
                    return data['stories']
                elif isinstance(data, list):
                    return data
        except Exception as e:
            # Fall back to direct JSON parsing
            pass

    # Fall back to direct JSON parsing
    if os.path.exists(backlog_path):
        try:
            with open(backlog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'stories' in data:
                stories = data['stories']
            elif isinstance(data, list):
                stories = data
            else:
                return []

            # Filter by status if needed
            filtered = [s for s in stories if s.get('status', '').lower() == status.lower()]
            return filtered if filtered else stories

        except Exception as e:
            return []

    return stories


def search_in_code(keywords, src_dir):
    """
    Search for keywords in source code.
    Returns True if any keyword is found.
    """
    if not keywords:
        return True  # No keywords to search = assume covered

    found_keywords = set()

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for keyword in keywords:
                        # Case-insensitive search for the keyword
                        # Use word boundaries to avoid partial matches
                        pattern = r'\b' + re.escape(keyword) + r'\b'
                        if re.search(pattern, content, re.IGNORECASE):
                            found_keywords.add(keyword)
                except:
                    pass

        # Early exit if all keywords found
        if len(found_keywords) == len(keywords):
            break

    return len(found_keywords) > 0, found_keywords


def check_ac_coverage(backlog_script, backlog_path, src_dir, status):
    """
    Main function to check acceptance criteria coverage.
    """
    stories = get_stories_from_backlog(backlog_script, backlog_path, status)

    if not stories:
        return {
            "status": "no_stories",
            "message": f"No stories found with status '{status}'",
            "stories": [],
            "summary": "No stories to check"
        }

    coverage_results = []

    for story in stories:
        story_id = story.get('id', story.get('title', 'Unknown'))
        title = story.get('title', 'Unknown')
        acs = story.get('acceptance_criteria', [])

        if isinstance(acs, str):
            # Single AC as string
            acs = [acs]

        covered_count = 0
        uncovered_acs = []

        for ac in acs:
            if not ac or not isinstance(ac, str):
                continue

            keywords = extract_keywords_from_ac(ac)
            found, matched_keywords = search_in_code(keywords, src_dir)

            if found:
                covered_count += 1
            else:
                uncovered_acs.append({
                    "ac": ac[:200],  # Truncate long ACs
                    "keywords_searched": keywords,
                    "reason": "No code references found"
                })

        total_acs = len([a for a in acs if a and isinstance(a, str)])

        coverage_results.append({
            "id": story_id,
            "title": title,
            "total_acs": total_acs,
            "covered_acs": covered_count,
            "uncovered_acs": uncovered_acs
        })

    # Determine overall status
    total_stories = len(coverage_results)
    stories_with_gaps = len([s for s in coverage_results if len(s['uncovered_acs']) > 0])

    if stories_with_gaps == 0:
        overall_status = "all_covered"
    elif stories_with_gaps < total_stories / 2:
        overall_status = "mostly_covered"
    else:
        overall_status = "gaps_found"

    result = {
        "status": overall_status,
        "stories": coverage_results,
        "summary": f"{stories_with_gaps} of {total_stories} stories have uncovered acceptance criteria"
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Check acceptance criteria coverage in code'
    )
    parser.add_argument('--backlog-script', required=True, help='Path to backlog_manager.py')
    parser.add_argument('--backlog-path', required=True, help='Path to backlog.json')
    parser.add_argument('--src', required=True, help='Path to source directory')
    parser.add_argument('--status', default='In Review', help='Story status to check (default: In Review)')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.backlog_path):
        print(json.dumps({
            "error": f"Backlog file not found: {args.backlog_path}"
        }), file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.src):
        print(json.dumps({
            "error": f"Source directory not found: {args.src}"
        }), file=sys.stderr)
        sys.exit(1)

    result = check_ac_coverage(args.backlog_script, args.backlog_path, args.src, args.status)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
