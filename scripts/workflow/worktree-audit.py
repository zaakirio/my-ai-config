#!/usr/bin/env python3
"""Classify git worktrees for cleanup; with --prune, remove only the clean, finished, idle ones.

Adapted from pstack's worktree-audit.sh. Branch refs survive removal, so a pruned
worktree is recoverable with `git worktree add <path> <branch>`.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
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


def worktrees(main, include_primary):
    rows, current = [], {}
    for line in git(main, 'worktree', 'list', '--porcelain').splitlines() + ['']:
        if not line:
            if current:
                rows.append(current)
            current = {}
            continue
        key, _, value = line.partition(' ')
        current[key] = value or True
    return rows if include_primary else rows[1:]


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
    # Use the time inside the last HEAD reflog entry (commit, checkout, reset). File mtimes are noise:
    # `git status` rewrites the index and git maintenance rewrites the reflog file.
    gitdir = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-dir'))
    log = gitdir / 'logs/HEAD'
    if log.exists():
        lines = log.read_text(errors='replace').splitlines()
        if lines:
            return int(lines[-1].split('\t', 1)[0].split()[-2])
    return int(git(path, 'log', '-1', '--format=%ct', check=False) or 0)


def size_kb(path):
    result = subprocess.run(['du', '-sk', str(path)], text=True, capture_output=True)
    return int(result.stdout.split()[0]) if result.stdout else 0


def process_cwds():
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        if proc.name == str(os.getpid()):
            continue
        try:
            found.append(((proc / 'cwd').readlink(), {'pid': int(proc.name), 'name': (proc / 'comm').read_text().strip()}))
        except (OSError, UnicodeError):
            continue
    return found


def classify(row, main_path, base, prs, recent_hours, now, processes):
    path = Path(row['worktree'])
    branch = row.get('branch', '').removeprefix('refs/heads/')
    working = [info for cwd, info in processes if cwd.is_relative_to(path)]
    signals = {'processes': working, 'locked': 'locked' in row,
               'lockReason': row['locked'] if isinstance(row.get('locked'), str) else None}
    if 'prunable' in row or not path.exists():
        # Git no longer tracks this checkout; `git worktree prune` drops the record, and any leftover directory is reported, not deleted.
        return {'worktree': str(path), 'branch': branch or 'detached', 'sizeKb': size_kb(path) if path.exists() else 0, 'idleHours': None,
                'merged': False, 'pr': '-', 'tracked': None, 'untracked': None, 'claim': None, 'bucket': 'broken', **signals}
    active = last_activity(path)
    status = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(path),
                             'status', '--porcelain=v1', '-z', '--no-renames', '--untracked-files=normal'], capture_output=True)
    tracked = untracked = None
    if status.returncode == 0:
        entries = [entry for entry in status.stdout.split(b'\0') if entry]
        untracked = sum(entry.startswith(b'?? ') for entry in entries)
        tracked = len(entries) - untracked
    merged = bool(row.get('HEAD')) and subprocess.run(['git', '-C', str(path), 'merge-base', '--is-ancestor', row['HEAD'], base]).returncode == 0
    pr = prs.get(branch, '-') if branch else '-'
    owner = claim(path) if branch else None
    idle_hours = (now - active) / 3600 if active else None
    if path == main_path:
        bucket = 'primary'
    elif signals['locked']:
        bucket = 'hold-locked'
    elif owner:
        bucket = 'hold-claimed'
    elif tracked is None:
        bucket = 'review'
    elif tracked:
        bucket = 'hold-wip'
    elif pr.endswith(('/open', '/draft')):
        bucket = 'hold-open-pr'
    elif working or (idle_hours is not None and idle_hours < recent_hours):
        bucket = 'active'
    elif (merged or pr.endswith(('/merged', '/closed'))) and not untracked:
        bucket = 'safe'
    else:
        bucket = 'review'
    return {
        'worktree': str(path), 'branch': branch or 'detached', 'sizeKb': size_kb(path),
        'idleHours': round(idle_hours) if idle_hours is not None else None, 'merged': merged, 'pr': pr,
        'tracked': tracked, 'untracked': untracked, 'claim': owner, 'bucket': bucket, **signals,
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
    parser.add_argument('--include-primary', action='store_true', help='Include the primary checkout in disk totals; never prune it')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--prune', action='store_true', help="Remove every worktree in the 'safe' bucket and the git records of 'broken' ones")
    args = parser.parse_args()

    now, rows = time.time(), []
    processes = process_cwds()
    for main_path in repos_from(args):
        base = base_ref(main_path, args.base)
        if base.startswith('origin/') and not args.offline:
            if subprocess.run(['git', '-C', str(main_path), 'fetch', '-q', 'origin', f'+refs/heads/{base[7:]}:refs/remotes/{base}'],
                              capture_output=True, timeout=120).returncode:
                print(f'warn: could not fetch {base} in {main_path}; MERGED may be stale', file=sys.stderr)
        prs = pull_requests(main_path, args.offline)
        with ThreadPoolExecutor(max_workers=8) as pool:
            for result in pool.map(lambda row: classify(row, main_path, base, prs, args.recent_hours, now, processes),
                                   worktrees(main_path, args.include_primary)):
                rows.append({'repo': str(main_path), 'base': base, **result})
    rows.sort(key=lambda r: r['sizeKb'], reverse=True)

    removed = []
    if args.prune:
        for row in (r for r in rows if r['bucket'] == 'safe'):
            result = subprocess.run(['git', '-C', row['repo'], 'worktree', 'remove', row['worktree']], text=True, capture_output=True)
            if result.returncode:
                print(f"warn: kept {row['worktree']}: {result.stderr.strip()}", file=sys.stderr)
            else:
                removed.append(row)
        for repo in {r['repo'] for r in rows if r in removed or r['bucket'] == 'broken'}:
            git(repo, 'worktree', 'prune')

    if args.json:
        print(json.dumps({'worktrees': rows, 'removed': [r['worktree'] for r in removed]}, indent=2))
        return
    print('SIZE\tIDLE\tMERGED\tPR\tTRACKED\tUNTRACKED\tCLAIM\tLOCK\tPIDS\tBUCKET\tBRANCH\tWORKTREE')
    for r in rows:
        idle = '?' if r['idleHours'] is None else f"{r['idleHours']}h"
        print('\t'.join([human(r['sizeKb']), idle, 'yes' if r['merged'] else 'no', r['pr'], str(r['tracked']), str(r['untracked']),
                         r['claim'] or '-', r['lockReason'] or ('locked' if r['locked'] else '-'),
                         ','.join(str(p['pid']) for p in r['processes']) or '-', r['bucket'], r['branch'], r['worktree']]))
    safe = sum(r['sizeKb'] for r in rows if r['bucket'] == 'safe')
    verb = 'removed' if args.prune else 'reclaimable with --prune'
    print(f"# {len(rows)} worktrees, {human(sum(r['sizeKb'] for r in rows))} total, {human(sum(r['sizeKb'] for r in removed) if args.prune else safe)} {verb}")


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(2)
