import json
import os
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
        old = time.time() - 10 * 86400
        for name, path in self.trees.items():
            if name == 'recent':
                continue
            gitdir = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-dir'))
            for entry in ['HEAD', 'index', 'logs/HEAD']:
                if (gitdir / entry).exists():
                    os.utime(gitdir / entry, (old, old))
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
            'recent': 'active', 'claimed': 'hold-claimed',
        })

    def test_prune_removes_only_safe_and_keeps_branches(self):
        result = self.audit('--prune')
        self.assertEqual([Path(p).name for p in result['removed']], ['merged'])
        self.assertFalse(self.trees['merged'].exists())
        for name in ['wip', 'scratch', 'unmerged', 'recent', 'claimed']:
            self.assertTrue(self.trees[name].exists(), name)
        self.assertIn('merged', git(self.repo, 'branch', '--list', 'merged'))


if __name__ == '__main__':
    unittest.main()
