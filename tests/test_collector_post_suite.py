"""Black-box tests: actual collector copied into isolated disposable Git repositories."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
COLLECTOR = Path(os.environ.get("COLLECTOR_UNDER_TEST", str(BASE / "twin" / "collect_attestation.py")))


def cmd(root: Path, *args):
    p = subprocess.run(args, cwd=root, text=True, capture_output=True, check=False)
    if p.returncode:
        raise AssertionError((args, p.returncode, p.stdout, p.stderr))
    return p.stdout.strip()


def make_repo(root: Path, scenario: str):
    (root / "twin").mkdir()
    (root / "tests").mkdir()
    shutil.copy2(COLLECTOR, root / "twin" / "collect_attestation.py")
    (root / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf8")
    (root / "AGENTS.md").write_text("SAFE_BASELINE\n", encoding="utf8")
    (root / "twin" / "environment-bridge.yaml").write_text("spec: fixed\n", encoding="utf8")
    (root / "twin" / "integration-registry.yaml").write_text("tool: denied\n", encoding="utf8")
    (root / "twin" / "ENVIRONMENT_BRIDGE.md").write_text("bridge fixed\n", encoding="utf8")
    (root / "twin" / "MEMORY_POLICY.md").write_text("memory fixed\n", encoding="utf8")
    scenarios = {
        "clean": "pass",
        "change_tracked": "from pathlib import Path\nPath('AGENTS.md').write_text('MUTATED_AFTER_INITIAL_CHECK\\n')",
        "add_untracked": "from pathlib import Path\nPath('ADDED_BY_TEST.txt').write_text('test side-effect')",
        "advance_head": "from pathlib import Path\nimport subprocess\nPath('AGENTS.md').write_text('NEW_COMMIT_AFTER_INITIAL_CHECK')\nsubprocess.run(['git','add','AGENTS.md'],check=True)\nsubprocess.run(['git','commit','-qm','revised during test'],check=True)",
        "change_origin": "import subprocess\nsubprocess.run(['git','remote','set-url','origin','https://github.com/untrusted/redirect.git'],check=True)",
        "rename_branch": "import subprocess\nsubprocess.run(['git','branch','-m','test/renamed-during-suite'],check=True)",
    }
    snippet = scenarios[scenario]
    source = (
        "import unittest\n"
        "class TestCase(unittest.TestCase):\n"
        "  def test_case(self):\n"
        + "    " + snippet.replace("\n", "\n    ") + "\n"
    )
    (root / "tests" / "test_suite.py").write_text(source, encoding="utf8")
    cmd(root, "git", "init", "-q", "-b", "test/twin-fixture")
    cmd(root, "git", "config", "user.name", "RUMBO Test")
    cmd(root, "git", "config", "user.email", "noreply@example.test")
    cmd(root, "git", "remote", "add", "origin", "https://github.com/fscfede-beep/verifiable-agent-control-plane.git")
    cmd(root, "git", "add", ".")
    cmd(root, "git", "commit", "-qm", "base")
    assert cmd(root, "git", "status", "--porcelain") == ""


def invoke(root: Path):
    with tempfile.TemporaryDirectory() as outdir:
        output = Path(outdir) / "attestation.json"
        p = subprocess.run([sys.executable, str(root / 'twin' / 'collect_attestation.py'),
                           '--role', 'primary', '--id', 'A', '--out', str(output)],
                           cwd=root, capture_output=True, text=True, check=False, timeout=30)
        report = json.loads(output.read_text()) if output.exists() else None
        dirty = cmd(root, "git", "status", "--porcelain")
        return p, report, dirty


class CollectorPostSuiteSecurity(unittest.TestCase):
    def test_clean_suite_emits_clean_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "clean")
            p, report, dirty = invoke(root)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertEqual(report['tests'], 'PASS')
            self.assertIs(report['working_tree_clean'], True)
            self.assertEqual(dirty, '')

    def test_suite_modifies_tracked_file_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "change_tracked")
            p, report, dirty = invoke(root)
            self.assertIn('AGENTS.md', dirty)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIsNone(report)
            self.assertIn('FAIL-CLOSED', p.stdout)

    def test_suite_adds_untracked_file_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "add_untracked")
            p, report, dirty = invoke(root)
            self.assertIn('ADDED_BY_TEST.txt', dirty)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIsNone(report)
            self.assertIn('FAIL-CLOSED', p.stdout)

    def test_suite_moves_head_with_clean_tree_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "advance_head")
            before = cmd(root, "git", "rev-parse", "HEAD")
            p, report, dirty = invoke(root)
            after = cmd(root, "git", "rev-parse", "HEAD")
            self.assertNotEqual(before, after)
            self.assertEqual(dirty, '')
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIsNone(report)

    def test_suite_changes_origin_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "change_origin")
            p, report, dirty = invoke(root)
            self.assertEqual(dirty, '')
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIsNone(report)

    def test_suite_renames_branch_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "rename_branch")
            p, report, dirty = invoke(root)
            self.assertEqual(dirty, '')
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIsNone(report)

    def test_prior_dirty_tree_still_fails_before_suite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_repo(root, "clean")
            (root / 'AGENTS.md').write_text('DIRTY_FROM_START\n')
            p, report, dirty = invoke(root)
            self.assertEqual(p.returncode, 2)
            self.assertIsNone(report)
            self.assertIn('AGENTS.md', dirty)

if __name__ == '__main__':
    unittest.main(verbosity=2)
