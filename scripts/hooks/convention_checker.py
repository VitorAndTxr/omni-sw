#!/usr/bin/env python3
"""
Convention Checker

Validates code against conventions defined in CLAUDE.md.

Usage:
    python convention_checker.py --claude-md <path-to-CLAUDE.md> --src <path-to-src-dir>

Checks:
    - Forbidden patterns: Patterns marked as "forbidden" or "do not use" in CLAUDE.md
    - Naming conventions: Validates naming patterns (PascalCase, camelCase, snake_case)
    - File structure: Validates expected directory structure exists
    - Required patterns: Ensures "always use" or "must use" patterns are present
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


class ConventionRule:
    """Represents a single convention rule extracted from CLAUDE.md"""

    def __init__(self, rule_type, description, pattern):
        self.rule_type = rule_type  # 'forbidden', 'naming', 'required', 'file_structure'
        self.description = description
        self.pattern = pattern


def extract_rules_from_claude_md(claude_file):
    """
    Extract convention rules from CLAUDE.md.
    Looks for sections like: Conventions, Forbidden, Rules, Patterns, Do not, Always, Must, Never
    """
    rules = []

    if not os.path.exists(claude_file):
        return rules

    with open(claude_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    current_section = None
    current_rules_text = []

    for i, line in enumerate(lines):
        # Detect section headers
        if re.match(r'^#+\s+(Conventions|Rules|Patterns|Forbidden|Do Not|Do not|Always|Must|Never|Naming|File Structure|Directory Structure)', line, re.IGNORECASE):
            # Process previous section
            if current_section and current_rules_text:
                rules.extend(parse_section_rules(current_section, current_rules_text))

            current_section = line.lower()
            current_rules_text = []
        elif current_section:
            # Accumulate content for current section
            current_rules_text.append(line)

    # Process last section
    if current_section and current_rules_text:
        rules.extend(parse_section_rules(current_section, current_rules_text))

    return rules


def parse_section_rules(section_header, section_lines):
    """
    Parse rules from a specific section based on the section type.
    """
    rules = []
    text = '\n'.join(section_lines)

    # Determine rule type from section header
    if 'forbidden' in section_header or 'do not' in section_header or 'never' in section_header:
        rule_type = 'forbidden'
    elif 'naming' in section_header:
        rule_type = 'naming'
    elif 'file' in section_header or 'directory' in section_header:
        rule_type = 'file_structure'
    elif 'always' in section_header or 'must' in section_header or 'required' in section_header:
        rule_type = 'required'
    else:
        rule_type = 'general'

    # Extract individual rules (look for bullet points, numbered lists, code blocks)
    lines = section_lines

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines and header lines
        if not line or line.startswith('#'):
            continue

        # Bullet points
        if line.startswith('- ') or line.startswith('* '):
            rule_text = line[2:].strip()
            if rule_text:
                # Try to extract pattern from rule text
                pattern = extract_pattern_from_rule(rule_text, rule_type)
                if pattern:
                    rules.append(ConventionRule(
                        rule_type=rule_type,
                        description=rule_text,
                        pattern=pattern
                    ))

        # Numbered lists
        elif re.match(r'^\d+\.\s+', line):
            rule_text = re.sub(r'^\d+\.\s+', '', line).strip()
            if rule_text:
                pattern = extract_pattern_from_rule(rule_text, rule_type)
                if pattern:
                    rules.append(ConventionRule(
                        rule_type=rule_type,
                        description=rule_text,
                        pattern=pattern
                    ))

    return rules


def extract_pattern_from_rule(rule_text, rule_type):
    """
    Extract a searchable pattern from a rule description.
    """
    # Try to extract quoted strings first
    quoted = re.findall(r'["\']([^"\']+)["\']', rule_text)
    if quoted:
        return quoted[0]

    # Try to extract code patterns (backticks)
    code = re.findall(r'`([^`]+)`', rule_text)
    if code:
        return code[0]

    # For naming conventions, extract patterns
    if rule_type == 'naming':
        if 'PascalCase' in rule_text:
            return 'PascalCase'
        elif 'camelCase' in rule_text:
            return 'camelCase'
        elif 'snake_case' in rule_text:
            return 'snake_case'
        elif 'UPPER_CASE' in rule_text or 'SCREAMING_SNAKE_CASE' in rule_text:
            return 'UPPER_CASE'

    # For file structures
    if rule_type == 'file_structure':
        # Look for path patterns
        paths = re.findall(r'/[\w/\-\.]+', rule_text)
        if paths:
            return paths[0]

    # For forbidden patterns, try to extract meaningful strings
    if rule_type == 'forbidden':
        # Common patterns
        if 'console.log' in rule_text:
            return 'console\\.log'
        elif 'var ' in rule_text:
            return r'\bvar\s+'
        elif 'eval' in rule_text:
            return r'\beval\s*\('
        elif 'global' in rule_text and 'variable' in rule_text.lower():
            return r'global\s+\w+\s*='

    return None


def check_forbidden_patterns(rules, src_dir):
    """
    Check if forbidden patterns appear in source code.
    """
    violations = []
    forbidden_rules = [r for r in rules if r.rule_type == 'forbidden']

    if not forbidden_rules:
        return violations

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for rule in forbidden_rules:
                        if not rule.pattern:
                            continue

                        for line_num, line_content in enumerate(lines, 1):
                            try:
                                if re.search(rule.pattern, line_content):
                                    violations.append({
                                        "rule": rule.description,
                                        "file": filepath,
                                        "line": line_num,
                                        "snippet": line_content.strip()[:100]
                                    })
                            except re.error:
                                # Invalid regex pattern, skip
                                pass
                except:
                    pass

    return violations


def check_naming_conventions(rules, src_dir):
    """
    Check naming conventions in source files.
    """
    violations = []
    naming_rules = [r for r in rules if r.rule_type == 'naming']

    if not naming_rules:
        return violations

    # Extract expected naming patterns
    expected_patterns = {}
    for rule in naming_rules:
        if rule.pattern:
            expected_patterns[rule.pattern] = rule.description

    # For now, do a basic check on variable names in code
    # This is a heuristic and won't be perfect
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js')):  # Focus on TypeScript/JavaScript
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Look for variable declarations
                    var_pattern = r'\b(let|const|var)\s+([a-zA-Z_$]\w*)'
                    matches = re.finditer(var_pattern, content)

                    for match in matches:
                        var_name = match.group(2)

                        # Check against expected patterns
                        for pattern in expected_patterns:
                            if pattern == 'camelCase':
                                if not is_camel_case(var_name):
                                    violations.append({
                                        "rule": f"Expected camelCase for variables",
                                        "file": filepath,
                                        "line": content[:match.start()].count('\n') + 1,
                                        "snippet": var_name
                                    })
                            elif pattern == 'PascalCase':
                                if not is_pascal_case(var_name):
                                    violations.append({
                                        "rule": f"Expected PascalCase for classes",
                                        "file": filepath,
                                        "line": content[:match.start()].count('\n') + 1,
                                        "snippet": var_name
                                    })
                except:
                    pass

    return violations


def is_camel_case(name):
    """Check if name is in camelCase."""
    return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name))


def is_pascal_case(name):
    """Check if name is in PascalCase."""
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))


def check_file_structure(rules, src_dir):
    """
    Check if expected file structure exists.
    """
    violations = []
    structure_rules = [r for r in rules if r.rule_type == 'file_structure']

    if not structure_rules:
        return violations

    for rule in structure_rules:
        if not rule.pattern:
            continue

        # Normalize path
        expected_path = rule.pattern.lstrip('/')
        full_path = os.path.join(src_dir, expected_path)

        if not os.path.exists(full_path):
            violations.append({
                "rule": f"Missing expected directory/file structure",
                "file": expected_path,
                "line": 0,
                "snippet": f"Expected {rule.pattern} to exist"
            })

    return violations


def check_required_patterns(rules, src_dir):
    """
    Check if required patterns are present in code.
    """
    violations = []
    required_rules = [r for r in rules if r.rule_type == 'required']

    # This is a heuristic check - we look for patterns in the whole codebase
    for rule in required_rules:
        if not rule.pattern:
            continue

        found = False

        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

            for file in files:
                if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        try:
                            if re.search(rule.pattern, content, re.IGNORECASE):
                                found = True
                                break
                        except re.error:
                            pass
                    except:
                        pass

            if found:
                break

        if not found:
            violations.append({
                "rule": rule.description,
                "file": "N/A",
                "line": 0,
                "snippet": f"Required pattern not found in codebase"
            })

    return violations


def check_conventions(claude_file, src_dir):
    """
    Main function to check code conventions.
    """
    rules = extract_rules_from_claude_md(claude_file)

    violations = []
    violations.extend(check_forbidden_patterns(rules, src_dir))
    violations.extend(check_naming_conventions(rules, src_dir))
    violations.extend(check_file_structure(rules, src_dir))
    violations.extend(check_required_patterns(rules, src_dir))

    # Deduplicate violations
    unique_violations = []
    seen = set()
    for v in violations:
        key = (v['rule'], v['file'], v['line'])
        if key not in seen:
            unique_violations.append(v)
            seen.add(key)

    status = "pass" if not unique_violations else "violations_found"

    result = {
        "status": status,
        "violations": unique_violations,
        "checks_performed": len(rules),
        "violations_count": len(unique_violations),
        "summary": f"{len(unique_violations)} violation(s) found across {len(rules)} checks"
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Check code conventions against CLAUDE.md'
    )
    parser.add_argument('--claude-md', required=True, help='Path to CLAUDE.md')
    parser.add_argument('--src', required=True, help='Path to source directory')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.claude_md):
        print(json.dumps({
            "error": f"CLAUDE.md file not found: {args.claude_md}"
        }), file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.src):
        print(json.dumps({
            "error": f"Source directory not found: {args.src}"
        }), file=sys.stderr)
        sys.exit(1)

    result = check_conventions(args.claude_md, args.src)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
