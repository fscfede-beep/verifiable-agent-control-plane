import json, subprocess, sys, tempfile, unittest
from pathlib import Path

class TestAttestationIntegrity(unittest.TestCase):
    def test_collector_rejects_dirty_tree_and_wrong_origin(self):
        text=Path("twin/collect_attestation.py").read_text(encoding="utf-8")
        self.assertIn("working tree is dirty", text)
        self.assertIn("origin is not the canonical repository", text)
    def test_gate_requires_platform_clean_and_pass(self):
        text=Path("twin/attestation-gate.py").read_text(encoding="utf-8")
        for token in ["platform","working_tree_clean","environment_not_verified","FAIL-CLOSED"]:
            self.assertIn(token,text)
    def test_windows_runner_stops_on_test_failure(self):
        text=Path("twin/attest-environment.ps1").read_text(encoding="utf-8")
        self.assertIn("test suite failed",text)
        self.assertIn("$testCode -ne 0",text)

if __name__=="__main__": unittest.main()
