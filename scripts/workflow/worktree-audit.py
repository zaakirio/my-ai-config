#!/usr/bin/env python3
"""Classify git worktrees for cleanup; with --prune, remove only the clean, finished, idle ones.

Adapted from pstack's worktree-audit.sh. Branch refs survive removal, so a pruned
worktree is recoverable with `git worktree add <path> <branch>`.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def git(path, *args, check=True):
    result = subprocess.run(['git', '-C', str(path), *args], text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f'git {" ".join(args)} failed in {path}: {result.stderr.strip()}')
    return result.stdout.strip() if result.returncode == 0 else ''


def main_worktree(path):
    common = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    listing = git(common, 'worktree', 'list', '--porcelain')
    return Path(listing.splitlines()[0].removeprefix('worktree '))


def worktrees(main):
    rows, current = [], {}
    for line in git(main, 'worktree', 'list', '--porcelain').splitlines() + ['']:
        if not line:
            if current:
                rows.append(current)
            current = {}
            continue
        key, _, value = line.partition(' ')
        current[key] = value or True
    return [row for row in rows[1:] if Path(row['worktree']).exists()]


def base_ref(main, requested):
    candidates = [requested] if requested else [git(main, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD', check=False), 'origin/main', 'origin/master']
    for ref in filter(None, candidates):
        if git(main, 'rev-parse', '--verify', '--quiet', ref + '^{commit}', check=False):
            return ref
    raise RuntimeError(f'No base ref in {main}; pass --base <ref>.')


def pull_requests(main, offline):
    if offline or not shutil.which('gh') or 'github.com' not in git(main, 'remote', 'get-url', 'origin', check=False):
        return {}
    result = subprocess.run(['gh', 'pr', 'list', '--state', 'all', '--limit', '1000', '--json', 'number,state,headRefName'],
                            cwd=main, text=True, capture_output=True, timeout=60)
    if result.returncode:
        print(f'warn: gh pr list failed in {main}; PR column is empty', file=sys.stderr)
        return {}
    prs = {}
    for pr in json.loads(result.stdout):
        prs.setdefault(pr['headRefName'], f"#{pr['number']}/{pr['state'].lower()}")
    return prs


def claim(path):
    command = os.environ.get('PR_OWNER_BIN') or shutil.which('pr-owner')
    if not command:
        return None
    result = subprocess.run([command, 'status', '--repo', str(path)], text=True, capture_output=True, timeout=30)
    record = json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else None
    return record.get('owner') if record else None


def last_activity(path):
    # Read before `git status`, which refreshes the index and would reset its mtime.
    gitdir = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-dir'))
    stamps = [(gitdir / name).stat().st_mtime for name in ('HEAD', 'index', 'logs/HEAD') if (gitdir / name).exists()]
    return max(stamps, default=0)


def size_kb(path):
    result = subprocess.run(['du', '-sk', str(path)], text=True, capture_output=True)
    return int(result.stdout.split()[0]) if result.stdout else 0


def classify(row, base, prs, recent_hours, now):
    path = Path(row['worktree'])
    active = last_activity(path)
    branch = row.get('branch', '').removeprefix('refs/heads/')
    status = git(path, 'status', '--porcelain', check=False).splitlines()
    tracked = sum(not line.startswith('??') for line in status)
    untracked = len(status) - tracked
    merged = bool(row.get('HEAD')) and subprocess.run(['git', '-C', str(path), 'merge-base', '--is-ancestor', row['HEAD'], base]).returncode == 0
    pr = prs.get(branch, '-') if branch else '-'
    owner = claim(path) if branch else None
    idle_hours = (now - active) / 3600 if active else None
    if owner:
        bucket = 'hold-claimed'
    elif tracked:
        bucket = 'hold-wip'
    elif pr.endswith(('/open', '/draft')):
        bucket = 'hold-open-pr'
    elif idle_hours is not None and idle_hours < recent_hours:
        bucket = 'active'
    elif (merged or pr.endswith(('/merged', '/closed'))) and not untracked:
        bucket = 'safe'
    else:
        bucket = 'review'
    return {
        'worktree': str(path), 'branch': branch or 'detached', 'sizeKb': size_kb(path),
        'idleHours': round(idle_hours) if idle_hours is not None else None, 'merged': merged, 'pr': pr,
        'tracked': tracked, 'untracked': untracked, 'claim': owner, 'bucket': bucket,
    }


def repos_from(args):
    seeds = [Path(p).expanduser() for p in args.repos]
    for root in args.scan:
        root = Path(root).expanduser()
        if root.is_dir():
            seeds.extend(p for p in root.glob('*/*') if (p / '.git').exists())
    if not seeds:
        seeds = [Path.cwd()]
    mains = {}
    for seed in seeds:
        main = main_worktree(seed)
        mains[str(main)] = main
    return list(mains.values())


def human(kb):
    return f'{kb / 1048576:.1f}G' if kb >= 1048576 else f'{kb / 1024:.0f}M'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('repos', nargs='*', help='Any checkout or worktree of each repository; default is the current directory')
    parser.add_argument('--scan', action='append', default=[], help='Also audit repositories owning worktrees two levels below this directory, e.g. ~/.t3/worktrees')
    parser.add_argument('--base', help='Ref that MERGED checks against; default origin/HEAD, origin/main, origin/master')
    parser.add_argument('--recent-hours', type=float, default=72, help='Git activity newer than this keeps a worktree active (default 72)')
    parser.add_argument('--offline', action='store_true', help='Skip the GitHub PR lookup')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--prune', action='store_true', help="Remove every worktree in the 'safe' bucket, then git worktree prune")
    args = parser.parse_args()

    now, rows = time.time(), []
    for main_path in repos_from(args):
        base = base_ref(main_path, args.base)
        if base.startswith('origin/') and not args.offline:
            if subprocess.run(['git', '-C', str(main_path), 'fetch', '-q', 'origin', f'+refs/heads/{base[7:]}:refs/remotes/{base}'],
                              capture_output=True, timeout=120).returncode:
                print(f'warn: could not fetch {base} in {main_path}; MERGED may be stale', file=sys.stderr)
        prs = pull_requests(main_path, args.offline)
        for row in worktrees(main_path):
            rows.append({'repo': str(main_path), 'base': base, **classify(row, base, prs, args.recent_hours, now)})
    rows.sort(key=lambda r: r['sizeKb'], reverse=True)

    removed = []
    if args.prune:
        for row in (r for r in rows if r['bucket'] == 'safe'):
            result = subprocess.run(['git', '-C', row['repo'], 'worktree', 'remove', row['worktree']], text=True, capture_output=True)
            if result.returncode:
                print(f"warn: kept {row['worktree']}: {result.stderr.strip()}", file=sys.stderr)
            else:
                removed.append(row)
        for repo in {r['repo'] for r in removed}:
            git(repo, 'worktree', 'prune')

    if args.json:
        print(json.dumps({'worktrees': rows, 'removed': [r['worktree'] for r in removed]}, indent=2))
        return
    print('SIZE\tIDLE\tMERGED\tPR\tTRACKED\tUNTRACKED\tCLAIM\tBUCKET\tBRANCH\tWORKTREE')
    for r in rows:
        idle = '?' if r['idleHours'] is None else f"{r['idleHours']}h"
        print('\t'.join([human(r['sizeKb']), idle, 'yes' if r['merged'] else 'no', r['pr'], str(r['tracked']), str(r['untracked']),
                         r['claim'] or '-', r['bucket'], r['branch'], r['worktree']]))
    safe = sum(r['sizeKb'] for r in rows if r['bucket'] == 'safe')
    verb = 'removed' if args.prune else 'reclaimable with --prune'
    print(f"# {len(rows)} worktrees, {human(sum(r['sizeKb'] for r in rows))} total, {human(sum(r['sizeKb'] for r in removed) if args.prune else safe)} {verb}")


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(2)
