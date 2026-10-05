import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Installation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="portable config ")
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/config.py"), *args, "--home", str(self.home)], text=True, capture_output=True)
        return result.returncode, json.loads(result.stdout)

    def test_install_is_repeatable_and_every_client_reads_same_skill(self):
        self.assertEqual(self.run_cli("install")[0], 0)
        self.assertEqual(self.run_cli("install")[0], 0)
        self.assertEqual(self.run_cli("doctor")[0], 0)
        for parent in [".agents/skills", ".claude/skills", ".config/opencode/skills", ".pi/agent/skills"]:
            skill = self.home / parent / "zk-review/SKILL.md"
            self.assertEqual(skill.read_bytes(), (ROOT / "skills/zk-review/SKILL.md").read_bytes())
        self.assertTrue((self.home / ".config/my-ai-config/review/post-review.py").is_file())

    def test_dry_run_does_not_create_links(self):
        code, report = self.run_cli("install", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "planned")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_conflict_is_atomic_and_replacement_retains_bytes(self):
        target = self.home / ".config/agents.md"
        target.parent.mkdir()
        target.write_text("local rules to retain\n")
        self.assertEqual(self.run_cli("install")[0], 1)
        self.assertFalse((self.home / ".agents").exists())
        code, report = self.run_cli("install", "--replace")
        self.assertEqual(code, 0)
        backups = [Path(row["backup"]) for row in report["links"] if "backup" in row]
        self.assertEqual([p.read_text() for p in backups], ["local rules to retain\n"])
        self.assertEqual(target.resolve(), ROOT / "agents.md")

    def test_additional_profile_with_shared_skills_keeps_unrelated_data(self):
        self.run_cli("install")
        profile = self.home / "second seat"
        profile.mkdir()
        (profile / "skills").symlink_to(self.home / ".claude/skills")
        sentinel = self.home / ".claude/skills/unrelated"
        sentinel.mkdir()
        (sentinel / "data").write_text("keep")
        self.assertEqual(self.run_cli("install", "--claude-profile", str(profile))[0], 0)
        self.assertEqual((sentinel / "data").read_text(), "keep")
        self.assertEqual((profile / "CLAUDE.md").resolve(), ROOT / "agents.md")

    def test_broken_link_is_reported_not_followed(self):
        target = self.home / ".config/my-ai-config"
        target.parent.mkdir()
        target.symlink_to(self.home / "missing")
        code, report = self.run_cli("doctor")
        self.assertEqual(code, 1)
        self.assertTrue(any(row["status"] == "conflict" for row in report["links"]))


if __name__ == "__main__":
    unittest.main()
