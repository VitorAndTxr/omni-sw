"""
agency_cli scan -- Repository/project discovery and config extraction.

Usage:
    agency_cli scan repo --root <path>              # Scan single repo
    agency_cli scan discover --root <path>           # Discover all repos under root
    agency_cli scan stack --project-path <path>      # Detect stack for a project
    agency_cli scan env-vars --project-path <path>   # Extract environment variables
    agency_cli scan endpoints --project-path <path>  # Extract API endpoints
    agency_cli scan db-config --project-path <path>  # Extract database configs
"""

import argparse
import glob
import json
import os
import re


# Project root markers
PROJECT_MARKERS = [
    ".git", "*.sln", "package.json", "docker-compose.yml", "docker-compose.yaml",
    "*.csproj", "*.fsproj", "pyproject.toml", "setup.py", "requirements.txt",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
]

# Directories to skip during scanning
SKIP_DIRS = {
    'node_modules', 'bin', 'obj', 'dist', 'build', '__pycache__', 'venv', '.venv',
    '.git', '.vs', '.idea', 'coverage', '.next', '.nuxt', 'target', 'vendor',
}

# Stack detection patterns
STACK_PATTERNS = {
    ".NET": {"markers": ["*.csproj", "*.fsproj", "*.sln"], "entry_points": ["Program.cs", "Startup.cs"]},
    "Node.js": {"markers": ["package.json"], "entry_points": ["index.js", "index.ts", "main.ts", "server.ts"]},
    "Python": {"markers": ["pyproject.toml", "setup.py", "requirements.txt"], "entry_points": ["main.py", "app.py", "manage.py"]},
    "Go": {"markers": ["go.mod"], "entry_points": ["main.go"]},
    "Rust": {"markers": ["Cargo.toml"], "entry_points": ["src/main.rs", "src/lib.rs"]},
    "Java": {"markers": ["pom.xml", "build.gradle"], "entry_points": ["src/main/java"]},
}


def discover_repos(root: str) -> list[dict]:
    """Discover all project repositories under a root directory."""
    root = os.path.normpath(os.path.abspath(root))
    repos = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]

        rel_path = os.path.relpath(dirpath, root)

        for marker in PROJECT_MARKERS:
            if '*' in marker:
                # Glob pattern
                matches = glob.glob(os.path.join(dirpath, marker))
                if matches:
                    if dirpath not in repos:
                        repos[dirpath] = {
                            "name": os.path.basename(dirpath),
                            "path": dirpath,
                            "relative_path": rel_path,
                            "markers": [],
                        }
                    for m in matches:
                        repos[dirpath]["markers"].append(os.path.basename(m))
            else:
                if marker in filenames or marker in dirnames:
                    if dirpath not in repos:
                        repos[dirpath] = {
                            "name": os.path.basename(dirpath),
                            "path": dirpath,
                            "relative_path": rel_path,
                            "markers": [],
                        }
                    repos[dirpath]["markers"].append(marker)

    # Deduplicate: if a repo is nested inside another, keep the most specific
    result = list(repos.values())

    # Detect stack for each
    for repo in result:
        stack = detect_stack(repo["path"])
        repo["stack"] = stack

    return result


def detect_stack(project_path: str) -> dict:
    """Detect technology stack for a project."""
    detected = []

    for stack_name, config in STACK_PATTERNS.items():
        for marker in config["markers"]:
            if '*' in marker:
                if glob.glob(os.path.join(project_path, marker)):
                    detected.append(stack_name)
                    break
            elif os.path.exists(os.path.join(project_path, marker)):
                detected.append(stack_name)
                break

    # Detect framework
    framework = None
    if ".NET" in detected:
        # Check for ASP.NET, Worker, etc.
        for csproj in glob.glob(os.path.join(project_path, "**", "*.csproj"), recursive=True):
            try:
                with open(csproj, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'Microsoft.NET.Sdk.Web' in content:
                    framework = "ASP.NET"
                elif 'Microsoft.NET.Sdk.Worker' in content:
                    framework = ".NET Worker"
                # Detect target framework
                tfm = re.search(r'<TargetFramework>(.*?)</TargetFramework>', content)
                if tfm:
                    detected.append(f"TFM: {tfm.group(1)}")
            except Exception:
                pass

    if "Node.js" in detected:
        pkg_path = os.path.join(project_path, "package.json")
        if os.path.isfile(pkg_path):
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "next" in deps:
                    framework = "Next.js"
                elif "nuxt" in deps:
                    framework = "Nuxt"
                elif "express" in deps:
                    framework = "Express"
                elif "fastify" in deps:
                    framework = "Fastify"
                elif "react" in deps:
                    framework = "React"
                elif "vue" in deps:
                    framework = "Vue"
                elif "angular" in deps or "@angular/core" in deps:
                    framework = "Angular"
            except Exception:
                pass

    if "Python" in detected:
        # Check for Django, Flask, FastAPI
        for py_file in glob.glob(os.path.join(project_path, "**", "*.py"), recursive=True):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    first_lines = f.read(2000)
                if 'from django' in first_lines or 'import django' in first_lines:
                    framework = "Django"
                    break
                elif 'from flask' in first_lines or 'import flask' in first_lines:
                    framework = "Flask"
                    break
                elif 'from fastapi' in first_lines or 'import fastapi' in first_lines:
                    framework = "FastAPI"
                    break
            except Exception:
                continue

    # Detect Docker
    has_docker = os.path.isfile(os.path.join(project_path, "Dockerfile"))
    has_compose = (
        os.path.isfile(os.path.join(project_path, "docker-compose.yml")) or
        os.path.isfile(os.path.join(project_path, "docker-compose.yaml"))
    )

    return {
        "runtimes": detected,
        "framework": framework,
        "has_docker": has_docker,
        "has_docker_compose": has_compose,
    }


def extract_env_vars(project_path: str) -> dict:
    """Extract environment variables from config files."""
    env_vars = {}

    # .env.example
    env_example = os.path.join(project_path, ".env.example")
    if os.path.isfile(env_example):
        try:
            with open(env_example, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key = line.split('=', 1)[0].strip()
                        env_vars[key] = {"source": ".env.example"}
        except Exception:
            pass

    # docker-compose.yml
    for compose_name in ["docker-compose.yml", "docker-compose.yaml"]:
        compose_path = os.path.join(project_path, compose_name)
        if os.path.isfile(compose_path):
            try:
                with open(compose_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Simple regex extraction for environment vars
                for match in re.finditer(r'(?:environment:.*?)([\w_]+)(?:\s*[:=])', content):
                    key = match.group(1)
                    if key.isupper() or '_' in key:
                        env_vars[key] = {"source": compose_name}
                # ${VAR} references
                for match in re.finditer(r'\$\{(\w+)', content):
                    env_vars[match.group(1)] = {"source": compose_name}
            except Exception:
                pass

    # appsettings*.json (ConnectionStrings section)
    for appsettings in glob.glob(os.path.join(project_path, "**", "appsettings*.json"), recursive=True):
        try:
            with open(appsettings, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Extract env var references like ${VAR}
            text = json.dumps(data)
            for match in re.finditer(r'\$\{(\w+)\}', text):
                env_vars[match.group(1)] = {"source": os.path.basename(appsettings)}
        except Exception:
            pass

    # launchSettings.json
    for launch in glob.glob(os.path.join(project_path, "**", "launchSettings.json"), recursive=True):
        try:
            with open(launch, 'r', encoding='utf-8') as f:
                data = json.load(f)
            profiles = data.get("profiles", {})
            for profile_name, profile in profiles.items():
                for key in profile.get("environmentVariables", {}):
                    env_vars[key] = {"source": f"launchSettings.json/{profile_name}"}
        except Exception:
            pass

    return {"project_path": project_path, "env_vars": env_vars, "count": len(env_vars)}


def extract_endpoints(project_path: str) -> dict:
    """Extract API endpoints from source files."""
    endpoints = []

    # .NET Controllers
    for cs_file in glob.glob(os.path.join(project_path, "**", "Controllers", "**", "*.cs"), recursive=True):
        try:
            with open(cs_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Route attributes
            controller_route = re.search(r'\[Route\("([^"]+)"\)\]', content)
            base_route = controller_route.group(1) if controller_route else ""
            # HTTP method attributes
            for match in re.finditer(
                r'\[(Http(?:Get|Post|Put|Delete|Patch))(?:\("([^"]*)")?)?\].*?(?:public\s+\w+\s+(\w+))',
                content, re.DOTALL
            ):
                method = match.group(1).replace("Http", "").upper()
                route = match.group(2) or ""
                action = match.group(3)
                full_route = f"{base_route}/{route}".replace("//", "/").rstrip("/")
                endpoints.append({
                    "method": method,
                    "route": full_route,
                    "action": action,
                    "file": os.path.relpath(cs_file, project_path),
                })
        except Exception:
            continue

    # .NET Minimal API
    for cs_file in glob.glob(os.path.join(project_path, "**", "*.cs"), recursive=True):
        try:
            with open(cs_file, 'r', encoding='utf-8') as f:
                content = f.read()
            for match in re.finditer(
                r'\.Map(Get|Post|Put|Delete|Patch)\("([^"]+)"',
                content
            ):
                endpoints.append({
                    "method": match.group(1).upper(),
                    "route": match.group(2),
                    "action": "minimal_api",
                    "file": os.path.relpath(cs_file, project_path),
                })
        except Exception:
            continue

    # Express/Fastify routes
    for ext in ("*.ts", "*.js"):
        for js_file in glob.glob(os.path.join(project_path, "**", ext), recursive=True):
            if 'node_modules' in js_file:
                continue
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                for match in re.finditer(
                    r'(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)',
                    content, re.IGNORECASE
                ):
                    endpoints.append({
                        "method": match.group(1).upper(),
                        "route": match.group(2),
                        "file": os.path.relpath(js_file, project_path),
                    })
            except Exception:
                continue

    # Python FastAPI/Flask routes
    for py_file in glob.glob(os.path.join(project_path, "**", "*.py"), recursive=True):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # FastAPI decorators
            for match in re.finditer(
                r'@(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)',
                content, re.IGNORECASE
            ):
                endpoints.append({
                    "method": match.group(1).upper(),
                    "route": match.group(2),
                    "file": os.path.relpath(py_file, project_path),
                })
            # Flask decorators
            for match in re.finditer(
                r'@\w+\.route\([\'"]([^\'"]+)[\'"],\s*methods\s*=\s*\[([^\]]+)\]',
                content
            ):
                route = match.group(1)
                methods = re.findall(r'[\'"](\w+)[\'"]', match.group(2))
                for method in methods:
                    endpoints.append({
                        "method": method.upper(),
                        "route": route,
                        "file": os.path.relpath(py_file, project_path),
                    })
        except Exception:
            continue

    return {"project_path": project_path, "endpoints": endpoints, "count": len(endpoints)}


def extract_db_config(project_path: str) -> dict:
    """Extract database configurations (redact secrets)."""
    configs = []

    # appsettings*.json
    for appsettings in glob.glob(os.path.join(project_path, "**", "appsettings*.json"), recursive=True):
        try:
            with open(appsettings, 'r', encoding='utf-8') as f:
                data = json.load(f)
            conn_strings = data.get("ConnectionStrings", {})
            for name, conn in conn_strings.items():
                # Redact password
                redacted = re.sub(r'(?i)(password|pwd)\s*=\s*[^;]+', r'\1=***REDACTED***', str(conn))
                # Extract host and database name
                host_match = re.search(r'(?i)(?:server|host|data source)\s*=\s*([^;]+)', str(conn))
                db_match = re.search(r'(?i)(?:database|initial catalog)\s*=\s*([^;]+)', str(conn))
                configs.append({
                    "name": name,
                    "source": os.path.relpath(appsettings, project_path),
                    "connection_string_redacted": redacted,
                    "host": host_match.group(1).strip() if host_match else None,
                    "database": db_match.group(1).strip() if db_match else None,
                })
        except Exception:
            continue

    # Prisma schema
    for prisma in glob.glob(os.path.join(project_path, "**", "schema.prisma"), recursive=True):
        if 'node_modules' in prisma:
            continue
        try:
            with open(prisma, 'r', encoding='utf-8') as f:
                content = f.read()
            provider_match = re.search(r'provider\s*=\s*"(\w+)"', content)
            url_match = re.search(r'url\s*=\s*env\("(\w+)"\)', content)
            configs.append({
                "name": "prisma",
                "source": os.path.relpath(prisma, project_path),
                "provider": provider_match.group(1) if provider_match else None,
                "env_var": url_match.group(1) if url_match else None,
            })
        except Exception:
            continue

    # .env (database-related vars)
    for env_file in [".env", ".env.example", ".env.local"]:
        env_path = os.path.join(project_path, env_file)
        if os.path.isfile(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip()
                            if any(k in key.upper() for k in ['DATABASE', 'DB_', 'MONGO', 'REDIS', 'POSTGRES', 'MYSQL', 'SQL']):
                                # Redact value
                                configs.append({
                                    "name": key,
                                    "source": env_file,
                                    "value_redacted": "***REDACTED***",
                                })
            except Exception:
                continue

    return {"project_path": project_path, "db_configs": configs, "count": len(configs)}


def full_repo_scan(root: str) -> dict:
    """Full scan of a single repository."""
    root = os.path.normpath(os.path.abspath(root))
    stack = detect_stack(root)
    endpoints = extract_endpoints(root)
    db_config = extract_db_config(root)
    env_vars = extract_env_vars(root)

    return {
        "name": os.path.basename(root),
        "path": root,
        "stack": stack,
        "endpoints": endpoints,
        "db_config": db_config,
        "env_vars": env_vars,
    }


def handle_scan(args: list[str]) -> dict | list:
    if not args:
        raise ValueError("Subcommand required: repo, discover, stack, env-vars, endpoints, db-config")

    subcmd = args[0]

    if subcmd == "repo":
        parser = argparse.ArgumentParser(prog="agency_cli scan repo")
        parser.add_argument("--root", required=True)
        opts = parser.parse_args(args[1:])
        return full_repo_scan(opts.root)

    elif subcmd == "discover":
        parser = argparse.ArgumentParser(prog="agency_cli scan discover")
        parser.add_argument("--root", required=True)
        opts = parser.parse_args(args[1:])
        repos = discover_repos(opts.root)
        return {"root": opts.root, "repos": repos, "count": len(repos)}

    elif subcmd == "stack":
        parser = argparse.ArgumentParser(prog="agency_cli scan stack")
        parser.add_argument("--project-path", required=True)
        opts = parser.parse_args(args[1:])
        return detect_stack(opts.project_path)

    elif subcmd == "env-vars":
        parser = argparse.ArgumentParser(prog="agency_cli scan env-vars")
        parser.add_argument("--project-path", required=True)
        opts = parser.parse_args(args[1:])
        return extract_env_vars(opts.project_path)

    elif subcmd == "endpoints":
        parser = argparse.ArgumentParser(prog="agency_cli scan endpoints")
        parser.add_argument("--project-path", required=True)
        opts = parser.parse_args(args[1:])
        return extract_endpoints(opts.project_path)

    elif subcmd == "db-config":
        parser = argparse.ArgumentParser(prog="agency_cli scan db-config")
        parser.add_argument("--project-path", required=True)
        opts = parser.parse_args(args[1:])
        return extract_db_config(opts.project_path)

    else:
        raise ValueError(f"Unknown subcommand: {subcmd}")
