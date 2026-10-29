import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BASE = {
    "schema": "rumbo-twin-attestation/v4",
    "repository": "fscfede-beep/verifiable-agent-control-plane",
    "branch": "test/twin-signer-isolated-review-20261029",
    "commit": "a" * 40,
    "python": "3.13.17",
    "runtime_version": "3.13.17",
    "platform": "Linux-test",
    "twin_spec_digest": "1" * 64,
    "tool_policy_digest": "2" * 64,
    "twin_bridge_sha256": "3" * 64,
    "ag_file_sha256": "4" * 64,
    "integration_registry_sha256": "5" * 64,
    "memory_policy_sha256": "6" * 64,
    "working_tree_clean": True,
    "tests_command": "python -m unittest discover -s tests -v",
}


class TestAttestationTestsMustPass(unittest.TestCase):
    def run_gate(self, a, b):
        with tempfile.TemporaryDirectory() as td:
            pa, pb = Path(td) / "a.json", Path(td) / "b.json"
            pa.write_text(json.dumps(a), encoding="utf-8")
            pb.write_text(json.dumps(b), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "twin/attestation-gate.py", str(pa), str(pb)],
                capture_output=True,
                text=True,
            )

    def test_both_pass(self):
        a = {**BASE, "tests": "PASS", "environment_role": "primary", "environment_id": "A"}
        b = {**BASE, "tests": "PASS", "environment_role": "twin", "environment_id": "B"}
        self.assertEqual(self.run_gate(a, b).returncode, 0)

    def test_both_fail_cannot_pass(self):
        a = {**BASE, "tests": "FAIL", "environment_role": "primary", "environment_id": "A"}
        b = {**BASE, "tests": "FAIL", "environment_role": "twin", "environment_id": "B"}
        r = self.run_gate(a, b)
        self.assertEqual(r.returncode, 2)
        self.assertIn("environment_not_verified", r.stdout)


if __name__ == "__main__":
    unittest.main()
