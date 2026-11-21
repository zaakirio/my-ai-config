import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'scripts/workflow/worktree-audit.py'


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True, text=True, capture_output=True).stdout.strip()


class WorktreeAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        remote, self.repo = self.root / 'remote.git', self.root / 'repo'
        git(self.root, 'init', '-q', '--bare', '-b', 'main', str(remote))
        git(self.root, 'clone', '-q', str(remote), str(self.repo))
        git(self.repo, 'config', 'user.email', 'test@example.com')
        git(self.repo, 'config', 'user.name', 'Test')
        git(self.repo, 'commit', '-q', '--allow-empty', '-m', 'base')
        git(self.repo, 'push', '-q', 'origin', 'main')
        self.trees = {}
        for name in ['merged', 'wip', 'scratch', 'unmerged', 'recent', 'claimed']:
            path = self.root / name
            git(self.repo, 'worktree', 'add', '-q', '-b', name, str(path), 'main')
            self.trees[name] = path
        git(self.trees['unmerged'], 'commit', '-q', '--allow-empty', '-m', 'not on main')
        (self.trees['wip'] / 'tracked.txt').write_text('x')
        git(self.trees['wip'], 'add', 'tracked.txt')
        (self.trees['scratch'] / 'notes.txt').write_text('x')
        (self.repo / '.git/info/exclude').write_text('node_modules/\n')
        (self.trees['merged'] / 'node_modules').mkdir()
        (self.trees['merged'] / 'node_modules/big.js').write_text('x')
        old = int(time.time() - 10 * 86400)
        for name, path in self.trees.items():
            if name == 'recent':
                continue
            log = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-dir')) / 'logs/HEAD'
            # Old reflog entries in a freshly touched file: activity must come from the entry, not the mtime.
            log.write_text(re.sub(r' \d{9,} ([+-]\d{4})\t', f' {old} \\1\t', log.read_text()))
        stale = self.root / 'stale'
        git(self.repo, 'worktree', 'add', '-q', '-b', 'stale', str(stale), 'main')
        (stale / '.git').unlink()
        self.trees['stale'] = stale
        fake = self.root / 'pr-owner'
        fake.write_text('#!/bin/sh\ncase "$3" in *claimed) echo \'{"owner": "thread-1"}\' ;; *) echo null ;; esac\n')
        fake.chmod(0o755)
        self.env = {**os.environ, 'PR_OWNER_BIN': str(fake)}

    def tearDown(self):
        self.tmp.cleanup()

    def audit(self, *args):
        result = subprocess.run(['python3', str(AUDIT), str(self.repo), '--offline', '--json', *args],
                                text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_buckets_protect_work_and_activity(self):
        buckets = {Path(r['worktree']).name: r['bucket'] for r in self.audit()['worktrees']}
        self.assertEqual(buckets, {
            'merged': 'safe', 'wip': 'hold-wip', 'scratch': 'review', 'unmerged': 'review',
            'recent': 'active', 'claimed': 'hold-claimed', 'stale': 'broken',
        })

    def test_prune_removes_only_safe_and_keeps_branches(self):
        result = self.audit('--prune')
        self.assertEqual([Path(p).name for p in result['removed']], ['merged'])
        self.assertFalse(self.trees['merged'].exists())
        for name in ['wip', 'scratch', 'unmerged', 'recent', 'claimed']:
            self.assertTrue(self.trees[name].exists(), name)
        self.assertIn('merged', git(self.repo, 'branch', '--list', 'merged'))
        self.assertTrue(self.trees['stale'].exists(), 'a broken worktree directory is reported, not deleted')
        self.assertNotIn(str(self.trees['stale']), git(self.repo, 'worktree', 'list'))

    def test_unreadable_status_is_not_clean(self):
        tree = self.trees['merged']
        index = Path(git(tree, 'rev-parse', '--absolute-git-dir')) / 'index'
        index.write_bytes(b'bad index')
        row = next(r for r in self.audit()['worktrees'] if r['worktree'] == str(tree))
        self.assertEqual(row['bucket'], 'review')
        self.assertIsNone(row['tracked'])
        self.assertIsNone(row['untracked'])
        self.assertNotIn(str(tree), self.audit('--prune')['removed'])

    def test_primary_and_locked_are_reported_but_never_pruned(self):
        tree = self.trees['merged']
        git(self.repo, 'worktree', 'lock', '--reason', 'held for review', str(tree))
        result = self.audit('--include-primary', '--prune')
        rows = {r['worktree']: r for r in result['worktrees']}
        self.assertEqual(rows[str(self.repo)]['bucket'], 'primary')
        self.assertGreater(rows[str(self.repo)]['sizeKb'], 0)
        self.assertEqual(rows[str(tree)]['bucket'], 'hold-locked')
        self.assertEqual(rows[str(tree)]['lockReason'], 'held for review')
        self.assertEqual(result['removed'], [])

    @unittest.skipUnless(Path('/proc/self/cwd').exists(), 'Linux process working directories')
    def test_live_process_overrides_old_reflog(self):
        tree = self.trees['merged']
        with subprocess.Popen(['cat'], cwd=tree, stdin=subprocess.PIPE) as holder:
            try:
                row = next(r for r in self.audit()['worktrees'] if r['worktree'] == str(tree))
                self.assertEqual(row['bucket'], 'active')
                self.assertIn(holder.pid, [p['pid'] for p in row['processes']])
                self.assertNotIn(str(tree), self.audit('--prune')['removed'])
            finally:
                holder.communicate()


if __name__ == '__main__':
    unittest.main()
