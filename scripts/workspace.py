#!/usr/bin/env python3
"""Guard heavy local jobs and expire only their managed, completed artifacts."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

GIB = 1024 ** 3
DEFAULT_ROOT = Path.home() / ".cache/agent-work"


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def check(path, required, reserve):
    free = shutil.disk_usage(path).free
    if free < (required + reserve) * GIB:
        raise RuntimeError(f"Only {free / GIB:.1f} GiB free at {path}; need {required:g} GiB for the job plus {reserve:g} GiB reserve. From the project run: python3 ~/.config/my-ai-config/scripts/workflow/worktree-audit.py --offline --include-primary. Inspect ownership before retrying.")
    return {"freeGiB": round(free / GIB, 2), "requiredGiB": required, "reserveGiB": reserve}


def prune(root, days):
    removed = []
    for run in sorted((root / "runs").iterdir()):
        if run.is_symlink() or not run.is_dir() or (run / ".keep").exists():
            continue
        record = run / "run.json"
        if record.is_symlink() or not record.is_file():
            continue
        data = json.loads(record.read_text())
        if data.get("id") != run.name or not data.get("finishedAt"):
            continue
        if time.time() - data["finishedAt"] < days * 86400:
            continue
        lease = run / "lease"
        if lease.is_symlink() or not lease.is_file():
            continue
        with lease.open("r+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            # Keep the small completion record after bulky artifacts expire.
            save(root / "records" / (run.name + ".json"), data)
            shutil.rmtree(run)
            removed.append(run.name)
    return {"removed": removed, "retentionDays": days}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("check", "run"):
        command = sub.add_parser(action)
        command.add_argument("--required-gib", type=float, required=True, help="Estimated new disk writes, including install/build scratch space")
        command.add_argument("--reserve-gib", type=float, default=10)
        if action == "run":
            command.add_argument("--pin", action="store_true", help="Keep this run's artifacts until .keep is removed")
            command.add_argument("command", nargs=argparse.REMAINDER)
    command = sub.add_parser("prune")
    command.add_argument("--days", type=float, default=7)
    args = parser.parse_args()
    try:
        root = args.root.expanduser().absolute()
        # Refuse symlinked roots, including parents, before any deletion.
        if root.resolve() != root:
            raise RuntimeError("Managed artifact root must not contain symlinks. Choose a dedicated real directory.")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ("runs", "records"):
            path = root / name
            if path.is_symlink():
                raise RuntimeError(f"Refusing symlinked managed directory: {path}")
            path.mkdir(exist_ok=True, mode=0o700)
        # All management operations share this lock; children inherit it so a
        # killed supervisor cannot let cleanup race its still-running child.
        with (root / "job.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("A managed job is active. Let it finish before another install, build, or cleanup.") from None
            if args.action == "prune":
                if not math.isfinite(args.days) or args.days < 1:
                    raise RuntimeError("Retention must be at least one day; pin proof that must be retained.")
                print(json.dumps(prune(root, args.days)))
                return 0
            if any(not math.isfinite(value) or value < 0 for value in (args.required_gib, args.reserve_gib)):
                raise RuntimeError("Disk estimates must be finite and nonnegative.")
            report = check(Path.cwd(), args.required_gib, args.reserve_gib)
            check(root, args.required_gib, args.reserve_gib)
            if args.action == "check":
                print(json.dumps(report))
                return 0
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            if not command:
                raise RuntimeError("Supply a command after --.")
            run = root / "runs" / uuid.uuid4().hex
            run.mkdir(mode=0o700)
            data = {"id": run.name, "startedAt": time.time(), "cwd": os.getcwd(), **report}
            save(run / "run.json", data)
            if args.pin:
                (run / ".keep").touch()
            (run / "artifacts").mkdir()
            with (run / "lease").open("a+") as lease:
                fcntl.flock(lease, fcntl.LOCK_EX)
                env = {**os.environ, "AGENT_ARTIFACT_DIR": str(run / "artifacts")}
                print(f"Artifacts: {env['AGENT_ARTIFACT_DIR']}", file=sys.stderr, flush=True)
                result = subprocess.run(command, env=env, pass_fds=(lock.fileno(), lease.fileno()))
                data.update(finishedAt=time.time(), exitCode=result.returncode)
                save(run / "run.json", data)
                return result.returncode if result.returncode >= 0 else 128 - result.returncode
    except (RuntimeError, OSError, ValueError) as error:
        print(f"WORKSPACE STOPPED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
