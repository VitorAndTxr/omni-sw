"""
agency_cli diagram — Mermaid diagram generation from scan data.

Usage:
    agency_cli diagram er --input <scan-json> --output <path>
    agency_cli diagram endpoints --input <scan-json> --output <path>
    agency_cli diagram service-map --input <scan-json> --output <path>
    agency_cli diagram workflow --input <scan-json> --output <path>
"""

import argparse
import json
import os


def generate_er_diagram(scan_data: dict) -> str:
    """Generate Mermaid ER diagram from database configs."""
    lines = ["# Database Diagrams\n"]

    db_configs = scan_data.get("db_config", {}).get("db_configs", [])
    if not db_configs:
        # Try multi-repo format
        repos = scan_data.get("repos", [scan_data])
        db_configs = []
        for repo in repos:
            repo_db = repo.get("db_config", {}).get("db_configs", [])
            for c in repo_db:
                c["repo"] = repo.get("name", "unknown")
            db_configs.extend(repo_db)

    if not db_configs:
        lines.append("No database configurations found.\n")
        return "\n".join(lines)

    # Group by database name
    databases = {}
    for config in db_configs:
        db_name = config.get("database") or config.get("name", "unknown")
        if db_name not in databases:
            databases[db_name] = {"configs": [], "host": config.get("host")}
        databases[db_name]["configs"].append(config)

    for db_name, info in databases.items():
        lines.append(f"## {db_name}\n")
        if info.get("host"):
            lines.append(f"**Host:** `{info['host']}`\n")
        lines.append("```mermaid")
        lines.append("erDiagram")
        lines.append(f"    %% Database: {db_name}")
        lines.append(f"    %% Sources: {', '.join(c.get('source', '?') for c in info['configs'])}")
        lines.append("    %% Entity details require source code analysis")
        lines.append("    %% Populate with entity definitions from DbContext/Prisma/migrations")
        lines.append("```\n")

    return "\n".join(lines)


def generate_endpoint_catalog(scan_data: dict) -> str:
    """Generate endpoint catalog markdown."""
    lines = ["# API Endpoint Catalog\n"]

    # Handle single repo or multi-repo
    repos = scan_data.get("repos", [scan_data])

    for repo in repos:
        repo_name = repo.get("name", "unknown")
        endpoints_data = repo.get("endpoints", {})
        endpoints = endpoints_data.get("endpoints", []) if isinstance(endpoints_data, dict) else []

        if not endpoints:
            continue

        lines.append(f"## {repo_name}\n")
        lines.append(f"**Total endpoints:** {len(endpoints)}\n")
        lines.append("| Method | Route | Action | File |")
        lines.append("|--------|-------|--------|------|")

        for ep in sorted(endpoints, key=lambda e: (e.get("route", ""), e.get("method", ""))):
            method = ep.get("method", "?")
            route = ep.get("route", "?")
            action = ep.get("action", "")
            file = ep.get("file", "")
            lines.append(f"| `{method}` | `{route}` | {action} | `{file}` |")

        lines.append("")

    if len(lines) <= 2:
        lines.append("No API endpoints found.\n")

    return "\n".join(lines)


def generate_service_map(scan_data: dict) -> str:
    """Generate Mermaid service map diagram."""
    lines = ["# Service Map\n"]
    lines.append("```mermaid")
    lines.append("graph TB")

    repos = scan_data.get("repos", [scan_data])

    # Group by stack
    services = []
    databases = set()

    for repo in repos:
        name = repo.get("name", "unknown")
        stack = repo.get("stack", {})
        runtimes = stack.get("runtimes", [])
        framework = stack.get("framework", "")

        safe_name = name.replace("-", "_").replace(".", "_")
        label = f"{name}"
        if framework:
            label += f"<br/>{framework}"
        elif runtimes:
            label += f"<br/>{runtimes[0]}"

        services.append(safe_name)
        lines.append(f"    {safe_name}[\"{label}\"]")

        # Database connections
        db_configs = repo.get("db_config", {}).get("db_configs", [])
        for db in db_configs:
            db_name = db.get("database") or db.get("name", "unknown_db")
            safe_db = "db_" + db_name.replace("-", "_").replace(".", "_")
            if safe_db not in databases:
                databases.add(safe_db)
                lines.append(f"    {safe_db}[(\"{db_name}\")]")
            lines.append(f"    {safe_name} --> {safe_db}")

    lines.append("```\n")
    return "\n".join(lines)


def generate_workflow_diagram(scan_data: dict) -> str:
    """Generate workflow diagrams for cross-service interactions."""
    lines = ["# Workflow Diagrams\n"]

    repos = scan_data.get("repos", [scan_data])
    if len(repos) <= 1:
        lines.append("Single-repo project — cross-service workflows not applicable.\n")
        lines.append("Use code analysis for internal workflow documentation.\n")
        return "\n".join(lines)

    # Generate a basic interaction diagram
    lines.append("## Service Interactions\n")
    lines.append("```mermaid")
    lines.append("sequenceDiagram")

    services = [r.get("name", "unknown") for r in repos]
    for i, svc in enumerate(services):
        lines.append(f"    participant {svc.replace('-', '_')}")

    lines.append("    Note over " + ",".join(s.replace("-", "_") for s in services) +
                  ": Interactions require source code analysis")
    lines.append("    %% Populate with actual inter-service call flows")
    lines.append("```\n")

    return "\n".join(lines)


def handle_diagram(args: list[str]) -> str:
    if not args:
        raise ValueError("Subcommand required: er, endpoints, service-map, workflow")

    subcmd = args[0]

    parser = argparse.ArgumentParser(prog=f"agency_cli diagram {subcmd}")
    parser.add_argument("--input", required=True, help="Path to scan result JSON")
    parser.add_argument("--output", required=True, help="Output file path")
    opts = parser.parse_args(args[1:])

    with open(opts.input, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)

    generators = {
        "er": generate_er_diagram,
        "endpoints": generate_endpoint_catalog,
        "service-map": generate_service_map,
        "workflow": generate_workflow_diagram,
    }

    if subcmd not in generators:
        raise ValueError(f"Unknown diagram type: {subcmd}. Valid: {', '.join(generators)}")

    content = generators[subcmd](scan_data)

    os.makedirs(os.path.dirname(os.path.abspath(opts.output)), exist_ok=True)
    with open(opts.output, 'w', encoding='utf-8') as f:
        f.write(content)

    return json.dumps({
        "diagram_type": subcmd,
        "output": opts.output,
        "size_chars": len(content),
        "size_tokens_est": len(content) // 4,
    })
