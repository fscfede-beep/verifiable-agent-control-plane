"""Regression: Twin environment IDs must never alias, even if other evidence matches."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "twin" / "attestation-gate.py"
BASE = {
    "schema": "rumbo-twin-attestation/v4",
    "repository": "fscfede-beep/verifiable-agent-control-plane",
    "commit": "a" * 40,
    "python": "3.13.17",
    "platform": "Linux-test",
    "twin_spec_digest": "x",
    "tool_policy_digest": "y",
    "ag_file_sha256": "z",
    "integration_registry_sha256": "q",
    "memory_policy_sha256": "m",
    "working_tree_clean": True,
    "tests": "PASS",
}

def verify(a, b):
    with tempfile.TemporaryDirectory() as td:
        pa, pb = Path(td) / "a.json", Path(td) / "b.json"
        pa.write_text(json.dumps(a), encoding="utf-8")
        pb.write_text(json.dumps(b), encoding="utf-8")
        p = subprocess.run([sys.executable, str(GATE), str(pa), str(pb)],
                           cwd=ROOT, text=True, capture_output=True, check=False)
        return p.returncode, p.stdout

def pair():
    return ({**BASE, "environment_role": "primary", "environment_id": "A"},
            {**BASE, "environment_role": "twin", "environment_id": "B"})

class TwinIdentityFailClosed(unittest.TestCase):
    def test_valid_pair_passes(self):
        a, b = pair()
        self.assertEqual(verify(a, b)[0], 0)

    def test_duplicated_a_id_fails_closed(self):
        a, b = pair()
        b["environment_id"] = "A"
        code, output = verify(a, b)
        self.assertEqual(code, 2)
        self.assertIn("invalid_environment_id", output)

    def test_swapped_ids_fail_closed(self):
        a, b = pair()
        a["environment_id"], b["environment_id"] = "B", "A"
        self.assertEqual(verify(a, b)[0], 2)

    def test_missing_id_fails_closed(self):
        a, b = pair()
        del b["environment_id"]
        self.assertEqual(verify(a, b)[0], 2)

    def test_missing_role_fails_closed(self):
        a, b = pair()
        del b["environment_role"]
        self.assertEqual(verify(a, b)[0], 2)

if __name__ == "__main__":
    unittest.main()
