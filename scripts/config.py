#!/usr/bin/env python3
"""Install or inspect the shared bundle without overwriting unrelated config."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = {
    "codex": (".codex/AGENTS.md", ".agents/skills"),
    "claude": (".claude/CLAUDE.md", ".claude/skills"),
    "opencode": (".config/opencode/AGENTS.md", ".config/opencode/skills"),
    "pi": (".pi/agent/AGENTS.md", ".pi/agent/skills"),
    "cursor": (None, ".cursor/skills"),
}


def links(home, clients, profiles):
    result = [(ROOT, home / ".config/my-ai-config")]
    # Existing Claude seats follow this shared file too.
    result.append((ROOT / "agents.md", home / ".config/agents.md"))
    for client in clients:
        rules, skills = CLIENTS[client]
        if rules:
            result.append((ROOT / "agents.md", home / rules))
        result.extend((skill, home / skills / skill.name) for skill in sorted((ROOT / "skills").iterdir()) if (skill / "SKILL.md").is_file())
        if client == "claude":
            result.extend((agent, home / ".claude/agents" / agent.name) for agent in sorted((ROOT / "agents").glob("*.md")))
    for profile in profiles:
        result.append((ROOT / "agents.md", profile / "CLAUDE.md"))
        result.extend((skill, profile / "skills" / skill.name) for skill in sorted((ROOT / "skills").iterdir()) if (skill / "SKILL.md").is_file())
        result.extend((agent, profile / "agents" / agent.name) for agent in sorted((ROOT / "agents").glob("*.md")))
    return result


def state(source, target):
    if target.is_symlink() and target.resolve() == source.resolve():
        return "ok"
    return "conflict" if target.exists() or target.is_symlink() else "missing"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["install", "doctor"])
    parser.add_argument("--home", type=Path, default=Path.home(), help="Destination home; useful for a clean-room installation check")
    parser.add_argument("--clients", nargs="+", choices=CLIENTS, default=["codex", "claude", "opencode", "pi"])
    parser.add_argument("--claude-profile", action="append", type=Path, default=[], help="Additional Claude config directory; repeat for each seat")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true", help="Back up conflicting files/links before replacing them; never discard them")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    pairs = links(home, args.clients, [p.expanduser().absolute() for p in args.claude_profile])
    rows = [{"source": str(s), "target": str(t), "status": state(s, t)} for s, t in pairs]
    conflicts = [r for r in rows if r["status"] == "conflict"]
    if args.command == "install" and not args.dry_run:
        if conflicts and not args.replace:
            print(json.dumps({"status": "blocked", "conflicts": conflicts, "next": "Review conflicts; rerun with --replace to retain backups."}, indent=2))
            return 1
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_root = home / ".config/my-ai-config-backups" / stamp
        for source, target in pairs:
            if state(source, target) == "ok":
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                # Keep numbered names so external Claude profiles cannot escape the backup root.
                backup_root.mkdir(parents=True, exist_ok=True)
                backup = backup_root / str(len(list(backup_root.iterdir())))
                target.rename(backup)
                rows.append({"target": str(target), "backup": str(backup)})
            target.symlink_to(source, target_is_directory=source.is_dir())
        rows = [{"source": str(s), "target": str(t), "status": state(s, t)} for s, t in pairs] + [r for r in rows if "backup" in r]
    problems = [r for r in rows if r.get("status") in ("conflict", "missing")]
    report = {"status": "planned" if args.dry_run else ("incomplete" if problems else "ok"), "bundle": str(ROOT), "links": rows}
    if args.command == "doctor":
        report["executables"] = {name: shutil.which(name) for name in ["python3", "git", "gh", *args.clients]}
        report["scope"] = "Filesystem discovery only; model, subagent, credential and live-session support must be checked in each client."
    print(json.dumps(report, indent=2))
    return 1 if problems and not args.dry_run else 0


if __name__ == "__main__":
    sys.exit(main())
