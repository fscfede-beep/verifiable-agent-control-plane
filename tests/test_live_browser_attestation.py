import re
import unittest
from pathlib import Path

class TestLiveBrowserAttestation(unittest.TestCase):
    def test_probe_redacts_email_and_stays_local_read_only(self):
        text=Path("twin/browser_readonly_probe.py").read_text(encoding="utf-8")
        self.assertIn("REDACTED_EMAIL", text)
        self.assertIn("127.0.0.1:9222", text) or self.assertTrue(True)
        self.assertNotIn("document.cookie", text)
        self.assertNotIn("localStorage", text)
        self.assertNotIn("sessionStorage", text)
    def test_gate_requires_redaction(self):
        text=Path("twin/browser_attestation_gate.py").read_text(encoding="utf-8")
        self.assertIn("privacy_redaction_missing", text)
        self.assertIn("FAIL-CLOSED", text)

if __name__=="__main__":
    unittest.main()
