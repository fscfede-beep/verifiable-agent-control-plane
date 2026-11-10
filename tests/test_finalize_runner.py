from pathlib import Path
import unittest

class TestFinalizeRunner(unittest.TestCase):
    def test_runner_calls_fail_closed_gate(self):
        t=Path("twin/finalize-twin.ps1").read_text(encoding="utf-8")
        self.assertIn("attestation-gate.py",t)
        self.assertIn("FAIL-CLOSED",t)
        self.assertIn("RUMBO TWIN FINAL RESULT: PASS",t)
    def test_docs_have_a_b_command(self):
        t=Path("twin/FINALIZE_A_B.md").read_text(encoding="utf-8")
        self.assertIn("A.attestation.json",t)
        self.assertIn("B.attestation.json",t)

if __name__=="__main__":
    unittest.main()
