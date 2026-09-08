from pathlib import Path
import unittest

class TestBrowserProbeSafety(unittest.TestCase):
    def test_probe_is_read_only_by_source_scan(self):
        text = Path("twin/browser_readonly_probe.py").read_text(encoding="utf-8")
        forbidden = [
            "Network.getAllCookies",
            "Storage.getCookies",
            "Page.navigate",
            "Input.dispatchMouseEvent",
            "Input.dispatchKeyEvent",
        ]
        for token in forbidden:
            self.assertNotIn(token, text)
        self.assertIn('"cookies_read": False', text)
        self.assertIn('"navigation": False', text)
        self.assertIn('"clicks": False', text)
        self.assertIn('"form_submission": False', text)

if __name__ == "__main__":
    unittest.main()
