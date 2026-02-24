#!/usr/bin/env python3
"""
Architecture Drift Check

Compares the architecture document against the actual implementation to detect drift.

Usage:
    python architecture_drift_check.py --architecture <path-to-ARCHITECTURE.md> --src <path-to-src-dir>

Checks:
    - Endpoints drift: Compares API endpoints in ARCHITECTURE.md vs actual route definitions
    - Data models drift: Checks entity/model names exist as classes/interfaces
    - Component drift: Checks component/service names exist as files/classes
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def extract_endpoints_from_architecture(arch_file):
    """
    Extract API endpoints from ARCHITECTURE.md.
    Looks for patterns like: GET /api/..., POST /api/..., or markdown tables.
    """
    endpoints = []

    if not os.path.exists(arch_file):
        return endpoints

    with open(arch_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: HTTP method + path (e.g., "GET /api/users", "POST /api/auth/login")
    pattern1 = r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(/[\w\-/]*)'
    matches = re.findall(pattern1, content, re.IGNORECASE)
    for method, path in matches:
        endpoints.append(f"{method.upper()} {path}")

    # Pattern 2: Markdown table with endpoint definitions
    # Looking for tables with "endpoint" or "path" columns
    lines = content.split('\n')
    in_table = False
    for i, line in enumerate(lines):
        if '|' in line and ('endpoint' in line.lower() or 'path' in line.lower() or 'method' in line.lower()):
            in_table = True
        elif in_table and '|' in line:
            # Extract cells from table row
            cells = [cell.strip() for cell in line.split('|')]
            # Look for patterns like "GET /api/users" in cells
            for cell in cells:
                if re.match(r'(GET|POST|PUT|DELETE|PATCH)\s+/\S+', cell, re.IGNORECASE):
                    endpoints.append(cell.strip())
        elif in_table and line.strip() == '':
            in_table = False

    return sorted(list(set(endpoints)))


def extract_models_from_architecture(arch_file):
    """
    Extract entity/model names from ARCHITECTURE.md.
    Looks for capitalized words that appear to be class names.
    """
    models = []

    if not os.path.exists(arch_file):
        return models

    with open(arch_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: Look for "Model", "Entity", "Class" followed by name, or capitalized names in certain contexts
    pattern = r'\b(User|Product|Order|Transaction|Account|Payment|Service|Controller|Repository|Manager|Handler|Factory|Builder|Validator|Processor|Manager|Engine|Worker|Provider|Client|Server|Manager|Store|Queue|Stream|Cache|Index|Schema|Type|Interface|Struct|Class|Entity|Model)\b'

    # More specific: look for capitalized identifiers
    pattern2 = r'\b([A-Z][a-zA-Z]+(?:Service|Controller|Repository|Entity|Model|Validator|Handler|Manager|Factory))\b'

    matches1 = re.findall(pattern, content)
    matches2 = re.findall(pattern2, content)

    models.extend(matches1)
    models.extend(matches2)

    return sorted(list(set(models)))


def extract_components_from_architecture(arch_file):
    """
    Extract component/service names from ARCHITECTURE.md.
    Looks for Service, Controller, Manager, Factory, etc. suffixes.
    """
    components = []

    if not os.path.exists(arch_file):
        return components

    with open(arch_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: Look for words ending in Service, Controller, Manager, etc.
    pattern = r'\b([A-Z][a-zA-Z]*(?:Service|Controller|Manager|Repository|Handler|Factory|Validator|Processor|Engine|Worker|Provider|Helper|Util|Middleware|Gateway|Client))\b'
    matches = re.findall(pattern, content)

    return sorted(list(set(matches)))


def find_endpoints_in_code(src_dir):
    """
    Find API endpoints defined in source code.
    Supports patterns for: Express, Django, Flask, ASP.NET, Spring, etc.
    """
    endpoints = []

    # Patterns to match endpoint definitions
    patterns = [
        (r'app\.(?:get|post|put|delete|patch|head|options)\s*\(\s*[\'"](/[^\'"]*)[\'"]', lambda m: f"INFERRED {m.group(1)}"),
        (r'router\.(?:get|post|put|delete|patch|head|options)\s*\(\s*[\'"](/[^\'"]*)[\'"]', lambda m: f"INFERRED {m.group(1)}"),
        (r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*[\'"]?(/[^\'"]*)[\'"]?', lambda m: f"INFERRED {m.group(1)}"),
        (r'\[Http(?:Get|Post|Put|Delete|Patch|Head|Options)\]', lambda m: "INFERRED"),
        (r'@(?:route|get|post|put|delete)\s*\(\s*[\'"](/[^\'"]*)[\'"]', lambda m: f"INFERRED {m.group(1)}"),
    ]

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern, extractor in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            try:
                                endpoint = extractor(match)
                                if endpoint and endpoint not in endpoints:
                                    endpoints.append(endpoint)
                            except:
                                pass
                except:
                    pass

    return sorted(list(set(endpoints)))


def find_models_in_code(src_dir):
    """
    Find class/interface definitions in source code.
    """
    models = set()

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Patterns for class/interface definitions
                    patterns = [
                        r'\b(?:class|interface|type|struct)\s+([A-Z][a-zA-Z0-9_]*)',
                        r'\b(?:export\s+)?(?:class|interface|type|struct)\s+([A-Z][a-zA-Z0-9_]*)',
                    ]

                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            models.add(match.group(1))
                except:
                    pass

    return sorted(list(models))


def find_components_in_code(src_dir):
    """
    Find component/service files in source code.
    Looks for files ending with Service, Controller, Manager, etc.
    """
    components = set()

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', 'bin', 'obj', '__pycache__']]

        for file in files:
            if file.endswith(('.ts', '.js', '.py', '.cs', '.java', '.go', '.rb', '.php')):
                # Remove extension
                name = file.rsplit('.', 1)[0]

                # Check if it matches component patterns (PascalCase with Service/Controller/etc suffix)
                if re.match(r'^[A-Z][a-zA-Z]*(?:Service|Controller|Manager|Repository|Handler|Factory|Validator|Processor|Engine|Worker|Provider|Helper|Util|Middleware|Gateway|Client)$', name):
                    components.add(name)

                # Also extract from class definitions in the file
                try:
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    pattern = r'\b(?:export\s+)?(?:class|interface)\s+([A-Z][a-zA-Z]*(?:Service|Controller|Manager|Repository|Handler|Factory|Validator|Processor))\b'
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        components.add(match.group(1))
                except:
                    pass

    return sorted(list(components))


def check_drift(architecture_file, src_dir):
    """
    Main function to check architecture drift.
    """
    # Extract from architecture
    documented_endpoints = extract_endpoints_from_architecture(architecture_file)
    documented_models = extract_models_from_architecture(architecture_file)
    documented_components = extract_components_from_architecture(architecture_file)

    # Find in code
    implemented_endpoints = find_endpoints_in_code(src_dir)
    found_models = find_models_in_code(src_dir)
    found_components = find_components_in_code(src_dir)

    # Compare endpoints
    doc_endpoints_set = set(documented_endpoints)
    impl_endpoints_set = set(implemented_endpoints)

    missing_in_code_endpoints = doc_endpoints_set - impl_endpoints_set
    undocumented_endpoints = impl_endpoints_set - doc_endpoints_set

    # Compare models
    doc_models_set = set(documented_models)
    found_models_set = set(found_models)

    missing_models = doc_models_set - found_models_set

    # Compare components
    doc_components_set = set(documented_components)
    found_components_set = set(found_components)

    missing_components = doc_components_set - found_components_set

    # Determine overall status
    total_issues = len(missing_in_code_endpoints) + len(missing_models) + len(missing_components)
    if total_issues == 0:
        status = "aligned"
    elif len(missing_in_code_endpoints) > 0 or len(missing_models) > 0 or len(missing_components) > 0:
        if total_issues < (len(documented_endpoints) + len(documented_models) + len(documented_components)) / 2:
            status = "partial"
        else:
            status = "drift_detected"
    else:
        status = "aligned"

    result = {
        "status": status,
        "endpoints": {
            "documented": documented_endpoints,
            "implemented": implemented_endpoints,
            "missing_in_code": sorted(list(missing_in_code_endpoints)),
            "undocumented_in_arch": sorted(list(undocumented_endpoints))
        },
        "models": {
            "documented": documented_models,
            "found_in_code": found_models,
            "missing_in_code": sorted(list(missing_models))
        },
        "components": {
            "documented": documented_components,
            "found_in_code": found_components,
            "missing_in_code": sorted(list(missing_components))
        },
        "summary": f"{total_issues} issues detected: {len(missing_in_code_endpoints)} endpoints, {len(missing_models)} models, {len(missing_components)} components missing in code"
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Check for architecture drift between documentation and implementation'
    )
    parser.add_argument('--architecture', required=True, help='Path to ARCHITECTURE.md')
    parser.add_argument('--src', required=True, help='Path to source directory')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.architecture):
        print(json.dumps({
            "error": f"Architecture file not found: {args.architecture}"
        }), file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.src):
        print(json.dumps({
            "error": f"Source directory not found: {args.src}"
        }), file=sys.stderr)
        sys.exit(1)

    result = check_drift(args.architecture, args.src)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
