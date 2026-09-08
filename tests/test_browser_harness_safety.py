from pathlib import Path
import unittest

class TestBrowserHarnessSafety(unittest.TestCase):
    def test_isolated_profiles_and_ports(self):
        text = Path("twin/start-twin-browser.ps1").read_text(encoding="utf-8")
        self.assertIn("PortA = 9222", text)
        self.assertIn("PortB = 9223", text)
        self.assertIn("RUMBO-Twin-$name", text)
        self.assertIn("--user-data-dir=$profile", text)
        self.assertIn("No copies cookies, tokens, passwords ni perfiles entre A y B", text)

    def test_harness_does_not_reference_external_network_debug_binding(self):
        text = Path("twin/start-twin-browser.ps1").read_text(encoding="utf-8")
        self.assertNotIn("--remote-debugging-address=0.0.0.0", text)

if __name__ == "__main__":
    unittest.main()
