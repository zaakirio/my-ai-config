import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/workspace.py"


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "managed"

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], capture_output=True, text=True)

    def run_job(self, source, *options):
        return self.cli("run", "--required-gib", "0", "--reserve-gib", "0", *options, "--", sys.executable, "-c", source)

    def test_insufficient_space_never_starts_the_command(self):
        marker = Path(self.temp.name) / "started"
        result = self.cli("run", "--required-gib", "1000000", "--", sys.executable, "-c", f"open({str(marker)!r}, 'w').close()")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("before retrying", result.stderr)
        self.assertIn("worktree-audit.py --offline --include-primary", result.stderr)
        self.assertFalse(marker.exists())

    def test_exit_code_and_artifacts_survive_and_arguments_are_not_logged(self):
        result = self.run_job("import os,pathlib; pathlib.Path(os.environ['AGENT_ARTIFACT_DIR'],'proof').write_text('keep'); raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)
        run = next((self.root / "runs").iterdir())
        data = json.loads((run / "run.json").read_text())
        self.assertEqual(data["exitCode"], 7)
        self.assertEqual((run / "artifacts/proof").read_text(), "keep")
        self.assertNotIn("raise SystemExit", (run / "run.json").read_text())

    def test_second_job_and_cleanup_refuse_while_first_job_holds_lock(self):
        ready = Path(self.temp.name) / "ready"
        first = subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(self.root), "run", "--required-gib", "0", "--reserve-gib", "0", "--", sys.executable, "-c", f"import pathlib,sys; pathlib.Path({str(ready)!r}).touch(); sys.stdin.read()"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(ready.exists())
            for args in [("prune",), ("run", "--required-gib", "0", "--", "true")]:
                blocked = self.cli(*args)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertIn("managed job is active", blocked.stderr)
        finally:
            first.communicate("", timeout=5)

    def test_retention_preserves_recent_pinned_aborted_and_external_data(self):
        self.assertEqual(self.run_job("pass").returncode, 0)
        recent = set((self.root / "runs").iterdir())
        self.assertEqual(self.run_job("pass", "--pin").returncode, 0)
        pinned = (set((self.root / "runs").iterdir()) - recent).pop()
        self.assertEqual(self.run_job("pass").returncode, 0)
        expired = (set((self.root / "runs").iterdir()) - recent - {pinned}).pop()
        for run in (pinned, expired):
            data = json.loads((run / "run.json").read_text())
            data["finishedAt"] = time.time() - 8 * 86400
            (run / "run.json").write_text(json.dumps(data))
        aborted = self.root / "runs/aborted"
        aborted.mkdir()
        (aborted / "run.json").write_text(json.dumps({"id": "aborted"}))
        outside = Path(self.temp.name) / "database"
        outside.mkdir()
        (outside / "data").write_text("preserve")
        (self.root / "runs/external").symlink_to(outside, target_is_directory=True)
        (expired / "external").symlink_to(outside, target_is_directory=True)
        result = self.cli("prune")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["removed"], [expired.name])
        self.assertEqual((outside / "data").read_text(), "preserve")
        self.assertTrue(pinned.exists())
        self.assertTrue(aborted.exists())
        self.assertTrue(all(run.exists() for run in recent))
        self.assertTrue((self.root / "records" / (expired.name + ".json")).exists())

    def test_symlinked_root_is_rejected(self):
        target = Path(self.temp.name) / "outside"
        target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        result = self.cli("prune")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(target.iterdir()), [])

    def test_nonfinite_estimates_and_retention_cannot_disable_guards(self):
        for args in [("prune", "--days", "nan"), ("prune", "--days", "0"), ("check", "--required-gib", "nan"), ("check", "--required-gib", "inf")]:
            self.assertNotEqual(self.cli(*args).returncode, 0, args)


if __name__ == "__main__":
    unittest.main()
