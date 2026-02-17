#!/usr/bin/env python3
"""
Backlog Manager — CRUD operations for the agency backlog system.
Manages user stories as structured JSON with role-based access control.

Usage:
    python backlog_manager.py <command> <backlog_path> [options]

Commands:
    create   <backlog_path> --id <US-XXX> --title <title> --role <user_role>
             --want <capability> --benefit <benefit> --feature <area>
             --priority <Must|Should|Could|Won't> --caller <po|pm|tl|dev|qa>
             [--notes <notes>] [--ac <AC JSON array>] [--depends <US-XXX,US-YYY>]

    edit     <backlog_path> --id <US-XXX> --caller <po|pm|tl|dev|qa>
             [--title <title>] [--role <user_role>] [--want <capability>]
             [--benefit <benefit>] [--priority <priority>] [--notes <notes>]
             [--ac <AC JSON array>] [--feature <area>] [--depends <US-XXX,US-YYY>]

    status   <backlog_path> --id <US-XXX> --status <new_status>
             --caller <po|pm|tl|dev|qa>

    list     <backlog_path> [--status <status>] [--feature <area>] [--priority <priority>]
             [--format <json|table|summary>] [--fields <field1,field2,...>]
             [--limit <N>] [--offset <N>]

    get      <backlog_path> --id <US-XXX>

    delete   <backlog_path> --id <US-XXX> --caller <po|pm|tl|dev|qa>

    init     <backlog_path>  (creates empty backlog structure)

    render   <backlog_path> --output <BACKLOG.md path>  (generates markdown summary)

    stats    <backlog_path>  (returns aggregate counts by status, priority, feature)

    question <backlog_path> --text <question_text> --caller <po|pm|tl|dev|qa>
             [--id <Q-XXX>] [--answer <answer_text>] [--resolve]

    next-id  <backlog_path>  (returns next available US-XXX id)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Access Control ---

PERMISSIONS = {
    "create": ["po", "pm"],
    "edit": ["po", "pm", "tl"],
    "status": ["po", "pm", "tl", "dev", "qa"],
    "delete": ["po", "pm"],
    "question": ["po", "pm", "tl", "dev", "qa"],
}

VALID_STATUSES = [
    "Draft",
    "Ready",
    "In Design",
    "Validated",
    "In Progress",
    "In Review",
    "In Testing",
    "Done",
    "Blocked",
    "Cancelled",
]

VALID_PRIORITIES = ["Must", "Should", "Could", "Won't"]


def check_permission(command: str, caller: str) -> bool:
    if command not in PERMISSIONS:
        return True
    return caller.lower() in PERMISSIONS[command]


# --- Backlog I/O ---


def load_backlog(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return create_empty_backlog()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_backlog(path: str, data: dict):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_empty_backlog() -> dict:
    return {
        "metadata": {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "stories": [],
        "questions": [],
    }


# --- Commands ---


def cmd_init(args):
    p = Path(args.backlog_path)
    if p.exists():
        print(json.dumps({"error": "Backlog already exists", "path": str(p)}))
        sys.exit(1)
    data = create_empty_backlog()
    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "path": str(p)}))


def cmd_create(args):
    if not check_permission("create", args.caller):
        print(json.dumps({"error": f"Permission denied: {args.caller} cannot create user stories. Only po, pm can."}))
        sys.exit(1)

    data = load_backlog(args.backlog_path)

    if any(s["id"] == args.id for s in data["stories"]):
        print(json.dumps({"error": f"Story {args.id} already exists"}))
        sys.exit(1)

    ac = []
    if args.ac:
        ac = json.loads(args.ac)

    depends = []
    if args.depends:
        depends = [d.strip() for d in args.depends.split(",")]

    story = {
        "id": args.id,
        "title": args.title,
        "feature_area": args.feature,
        "priority": args.priority,
        "role": args.role,
        "want": args.want,
        "benefit": args.benefit,
        "acceptance_criteria": ac,
        "notes": args.notes or "",
        "dependencies": depends,
        "status": "Draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": args.caller,
        "history": [
            {
                "action": "created",
                "by": args.caller,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }

    data["stories"].append(story)
    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "id": story["id"]}))


def cmd_edit(args):
    if not check_permission("edit", args.caller):
        print(json.dumps({"error": f"Permission denied: {args.caller} cannot edit user stories. Only po, pm, tl can."}))
        sys.exit(1)

    data = load_backlog(args.backlog_path)
    story = next((s for s in data["stories"] if s["id"] == args.id), None)
    if not story:
        print(json.dumps({"error": f"Story {args.id} not found"}))
        sys.exit(1)

    changes = {}
    for field in ["title", "role", "want", "benefit", "priority", "notes", "feature"]:
        val = getattr(args, field, None)
        if val is not None:
            key = "feature_area" if field == "feature" else field
            changes[key] = val
            story[key] = val

    if args.ac:
        ac = json.loads(args.ac)
        changes["acceptance_criteria"] = ac
        story["acceptance_criteria"] = ac

    if args.depends is not None:
        depends = [d.strip() for d in args.depends.split(",")] if args.depends else []
        changes["dependencies"] = depends
        story["dependencies"] = depends

    story["updated_at"] = datetime.now(timezone.utc).isoformat()
    story.setdefault("history", []).append(
        {
            "action": "edited",
            "by": args.caller,
            "changes": list(changes.keys()),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )

    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "id": args.id, "changes": list(changes.keys())}))


def cmd_status(args):
    if not check_permission("status", args.caller):
        print(json.dumps({"error": f"Permission denied: {args.caller} cannot change status."}))
        sys.exit(1)

    if args.status not in VALID_STATUSES:
        print(json.dumps({"error": f"Invalid status '{args.status}'. Valid: {VALID_STATUSES}"}))
        sys.exit(1)

    data = load_backlog(args.backlog_path)
    story = next((s for s in data["stories"] if s["id"] == args.id), None)
    if not story:
        print(json.dumps({"error": f"Story {args.id} not found"}))
        sys.exit(1)

    old_status = story["status"]
    story["status"] = args.status
    story["updated_at"] = datetime.now(timezone.utc).isoformat()
    story.setdefault("history", []).append(
        {
            "action": "status_change",
            "by": args.caller,
            "from": old_status,
            "to": args.status,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )

    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "id": args.id, "old_status": old_status, "new_status": args.status}))


AUDIT_FIELDS = {"history", "created_at", "updated_at", "created_by"}

LIST_DEFAULT_FIELDS = [
    "id", "title", "feature_area", "priority", "role", "want", "benefit",
    "acceptance_criteria", "notes", "dependencies", "status",
]

SUMMARY_DEFAULT_FIELDS = ["id", "title", "status", "priority", "feature_area"]


def _pick_fields(story: dict, fields: list[str]) -> dict:
    return {k: story.get(k, "-") for k in fields}


def cmd_list(args):
    data = load_backlog(args.backlog_path)
    stories = data["stories"]

    if args.status:
        stories = [s for s in stories if s["status"] == args.status]
    if args.feature:
        stories = [s for s in stories if s.get("feature_area") == args.feature]
    if args.priority:
        stories = [s for s in stories if s.get("priority") == args.priority]

    total = len(stories)

    if args.offset:
        stories = stories[args.offset:]
    if args.limit:
        stories = stories[: args.limit]

    custom_fields = None
    if args.fields:
        custom_fields = [f.strip() for f in args.fields.split(",")]

    fmt = args.format or "summary"

    if fmt == "json":
        fields = custom_fields or LIST_DEFAULT_FIELDS
        projected = [_pick_fields(s, fields) for s in stories]
        print(json.dumps({"stories": projected, "count": total}))
    elif fmt == "table":
        fields = custom_fields or ["id", "title", "priority", "status", "feature_area"]
        header = " | ".join(fields)
        sep = " | ".join("---" for _ in fields)
        lines = [header, sep]
        for s in stories:
            row = " | ".join(str(s.get(f, "-")) for f in fields)
            lines.append(row)
        print("\n".join(lines))
    else:
        fields = custom_fields or SUMMARY_DEFAULT_FIELDS
        projected = [_pick_fields(s, fields) for s in stories]
        print(json.dumps({"stories": projected, "count": total}))


def cmd_stats(args):
    data = load_backlog(args.backlog_path)
    stories = data["stories"]
    by_status = {}
    by_priority = {}
    by_feature = {}
    for s in stories:
        st = s.get("status", "Unknown")
        by_status[st] = by_status.get(st, 0) + 1
        pr = s.get("priority", "Unknown")
        by_priority[pr] = by_priority.get(pr, 0) + 1
        fa = s.get("feature_area", "Uncategorized")
        by_feature[fa] = by_feature.get(fa, 0) + 1
    print(json.dumps({
        "total": len(stories),
        "by_status": by_status,
        "by_priority": by_priority,
        "by_feature": by_feature,
    }))


def cmd_get(args):
    data = load_backlog(args.backlog_path)
    story = next((s for s in data["stories"] if s["id"] == args.id), None)
    if not story:
        print(json.dumps({"error": f"Story {args.id} not found"}))
        sys.exit(1)
    print(json.dumps({"story": story}))


def cmd_delete(args):
    if not check_permission("delete", args.caller):
        print(json.dumps({"error": f"Permission denied: {args.caller} cannot delete stories. Only po, pm can."}))
        sys.exit(1)

    data = load_backlog(args.backlog_path)
    idx = next((i for i, s in enumerate(data["stories"]) if s["id"] == args.id), None)
    if idx is None:
        print(json.dumps({"error": f"Story {args.id} not found"}))
        sys.exit(1)

    removed = data["stories"].pop(idx)
    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "deleted": removed["id"]}))


def cmd_render(args):
    data = load_backlog(args.backlog_path)
    stories = data["stories"]
    questions = data.get("questions", [])

    lines = [
        "<!-- AGENT NOTICE: This file is auto-generated and for HUMAN reading only.",
        "     DO NOT read this file to query backlog data. Use the backlog_manager.py script instead:",
        "     - Overview: python {script} stats {backlog_path}",
        "     - List:     python {script} list {backlog_path} --format summary",
        "     - Detail:   python {script} get {backlog_path} --id US-XXX",
        "     Reading this file wastes context tokens and may contain stale data. -->",
        "",
        "# Product Backlog",
        "",
    ]
    lines.append(f"> Auto-generated from `backlog.json` — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Group by feature area
    features = {}
    for s in stories:
        fa = s.get("feature_area", "Uncategorized")
        features.setdefault(fa, []).append(s)

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    status_counts = {}
    for s in stories:
        status_counts[s["status"]] = status_counts.get(s["status"], 0) + 1
    for st in VALID_STATUSES:
        if st in status_counts:
            lines.append(f"| {st} | {status_counts[st]} |")
    lines.append(f"| **Total** | **{len(stories)}** |")
    lines.append("")

    # Stories by feature
    lines.append("## User Stories")
    lines.append("")

    for feature, feature_stories in features.items():
        lines.append(f"### Feature Area: {feature}")
        lines.append("")
        for s in feature_stories:
            lines.append(f"#### {s['id']}: {s['title']}")
            lines.append("")
            lines.append(f"**Priority:** {s.get('priority', '-')} | **Status:** {s['status']}")
            lines.append("")
            lines.append(f"> As a *{s.get('role', '...')}*, I want *{s.get('want', '...')}*, so that *{s.get('benefit', '...')}*.")
            lines.append("")
            if s.get("acceptance_criteria"):
                lines.append("**Acceptance Criteria:**")
                lines.append("")
                for ac in s["acceptance_criteria"]:
                    ac_id = ac.get("id", "-")
                    given = ac.get("given", "...")
                    when = ac.get("when", "...")
                    then = ac.get("then", "...")
                    lines.append(f"- **{ac_id}:** Given *{given}*, when *{when}*, then *{then}*")
                lines.append("")
            if s.get("notes"):
                lines.append(f"**Notes:** {s['notes']}")
                lines.append("")
            if s.get("dependencies"):
                lines.append(f"**Depends on:** {', '.join(s['dependencies'])}")
                lines.append("")
            lines.append("---")
            lines.append("")

    # Dependency map
    deps = [(s["id"], d) for s in stories for d in s.get("dependencies", [])]
    if deps:
        lines.append("## Story Dependency Map")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph LR")
        for src, dst in deps:
            src_label = src.replace("-", "")
            dst_label = dst.replace("-", "")
            lines.append(f'    {src_label}["{src}"] --> {dst_label}["{dst}"]')
        lines.append("```")
        lines.append("")

    # Open questions
    if questions:
        lines.append("## Open Questions")
        lines.append("")
        lines.append("| # | Question | Status | Answer |")
        lines.append("|---|---------|--------|--------|")
        for q in questions:
            status = "Resolved" if q.get("resolved") else "Open"
            answer = q.get("answer", "-")
            lines.append(f"| {q['id']} | {q['text']} | {status} | {answer} |")
        lines.append("")

    md_content = "\n".join(lines)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(json.dumps({"success": True, "path": str(output_path), "stories": len(stories)}))


def cmd_question(args):
    if not check_permission("question", args.caller):
        print(json.dumps({"error": f"Permission denied."}))
        sys.exit(1)

    data = load_backlog(args.backlog_path)
    questions = data.setdefault("questions", [])

    if args.resolve and args.id:
        q = next((q for q in questions if q["id"] == args.id), None)
        if not q:
            print(json.dumps({"error": f"Question {args.id} not found"}))
            sys.exit(1)
        q["resolved"] = True
        if args.answer:
            q["answer"] = args.answer
        q["resolved_by"] = args.caller
        q["resolved_at"] = datetime.now(timezone.utc).isoformat()
        save_backlog(args.backlog_path, data)
        print(json.dumps({"success": True, "question": q}))
        return

    # Create new question
    q_id = args.id
    if not q_id:
        existing_ids = [int(q["id"].replace("Q-", "")) for q in questions if q["id"].startswith("Q-")]
        next_num = max(existing_ids, default=0) + 1
        q_id = f"Q-{next_num:03d}"

    question = {
        "id": q_id,
        "text": args.text,
        "asked_by": args.caller,
        "asked_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False,
        "answer": args.answer or "",
    }
    questions.append(question)
    save_backlog(args.backlog_path, data)
    print(json.dumps({"success": True, "question": question}))


def cmd_next_id(args):
    data = load_backlog(args.backlog_path)
    existing_ids = []
    for s in data["stories"]:
        sid = s["id"]
        if sid.startswith("US-"):
            try:
                existing_ids.append(int(sid.replace("US-", "")))
            except ValueError:
                pass
    next_num = max(existing_ids, default=0) + 1
    print(json.dumps({"next_id": f"US-{next_num:03d}"}))


# --- CLI ---


def main():
    parser = argparse.ArgumentParser(description="Backlog Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init")
    p_init.add_argument("backlog_path")

    # create
    p_create = subparsers.add_parser("create")
    p_create.add_argument("backlog_path")
    p_create.add_argument("--id", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--role", required=True)
    p_create.add_argument("--want", required=True)
    p_create.add_argument("--benefit", required=True)
    p_create.add_argument("--feature", required=True)
    p_create.add_argument("--priority", required=True, choices=VALID_PRIORITIES)
    p_create.add_argument("--caller", required=True)
    p_create.add_argument("--notes", default="")
    p_create.add_argument("--ac", default=None, help="JSON array of acceptance criteria")
    p_create.add_argument("--depends", default=None, help="Comma-separated US IDs")

    # edit
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("backlog_path")
    p_edit.add_argument("--id", required=True)
    p_edit.add_argument("--caller", required=True)
    p_edit.add_argument("--title")
    p_edit.add_argument("--role")
    p_edit.add_argument("--want")
    p_edit.add_argument("--benefit")
    p_edit.add_argument("--priority", choices=VALID_PRIORITIES)
    p_edit.add_argument("--notes")
    p_edit.add_argument("--feature")
    p_edit.add_argument("--ac")
    p_edit.add_argument("--depends")

    # status
    p_status = subparsers.add_parser("status")
    p_status.add_argument("backlog_path")
    p_status.add_argument("--id", required=True)
    p_status.add_argument("--status", required=True)
    p_status.add_argument("--caller", required=True)

    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("backlog_path")
    p_list.add_argument("--status")
    p_list.add_argument("--feature")
    p_list.add_argument("--priority")
    p_list.add_argument("--format", choices=["json", "table", "summary"], default="summary")
    p_list.add_argument("--fields", default=None, help="Comma-separated field names to return")
    p_list.add_argument("--limit", type=int, default=None, help="Max stories to return")
    p_list.add_argument("--offset", type=int, default=None, help="Skip first N stories")

    # stats
    p_stats = subparsers.add_parser("stats")
    p_stats.add_argument("backlog_path")

    # get
    p_get = subparsers.add_parser("get")
    p_get.add_argument("backlog_path")
    p_get.add_argument("--id", required=True)

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("backlog_path")
    p_delete.add_argument("--id", required=True)
    p_delete.add_argument("--caller", required=True)

    # render
    p_render = subparsers.add_parser("render")
    p_render.add_argument("backlog_path")
    p_render.add_argument("--output", required=True)

    # question
    p_question = subparsers.add_parser("question")
    p_question.add_argument("backlog_path")
    p_question.add_argument("--text", default="")
    p_question.add_argument("--caller", required=True)
    p_question.add_argument("--id", default=None)
    p_question.add_argument("--answer", default=None)
    p_question.add_argument("--resolve", action="store_true")

    # next-id
    p_nextid = subparsers.add_parser("next-id")
    p_nextid.add_argument("backlog_path")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "create": cmd_create,
        "edit": cmd_edit,
        "status": cmd_status,
        "list": cmd_list,
        "stats": cmd_stats,
        "get": cmd_get,
        "delete": cmd_delete,
        "render": cmd_render,
        "question": cmd_question,
        "next-id": cmd_next_id,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
