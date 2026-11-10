import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BASE = {
    "schema": "rumbo-twin-attestation/v4",
    "repository": "fscfede-beep/verifiable-agent-control-plane",
    "commit": "abc",
    "python": "3.13",
    "runtime_version": "3.13",
    "platform": "Linux-test",
    "twin_spec_digest": "spec",
    "tool_policy_digest": "policy",
    "twin_bridge_sha256": "bridge",
    "ag_file_sha256": "a",
    "integration_registry_sha256": "b",
    "memory_policy_sha256": "c",
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
