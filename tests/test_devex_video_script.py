import re
from pathlib import Path
import unittest

DOC = Path(__file__).parents[1] / "docs" / "YOUTUBE_AGENT_RELIABILITY_QUICKSTART_SCRIPT.md"

class DevExVideoScriptContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_has_devex_90_second_package_sections(self):
        for heading in (
            "## 90-second script",
            "## Shot list",
            "## YouTube metadata",
            "## LinkedIn copy",
            "## X copy",
        ):
            self.assertIn(heading, self.text)


    def test_spoken_script_fits_90_second_budget(self):
        match = re.search(
            r"## 90-second script\n\n(.*?)\n\n## Shot list",
            self.text,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        spoken = re.sub(r"`[^`]+`", "", match.group(1))
        words = re.findall(r"\b[\w'-]+\b", spoken)
        self.assertGreaterEqual(len(words), 140)
        self.assertLessEqual(len(words), 230)

    def test_core_state_drift_claims_are_visible(self):
        required = (
            "DECISION_ACCEPTED != EXECUTION_SAFE",
            "state drift after decision",
            "blocked_target_mutated=False",
            "REFERENCE_IMPLEMENTATION != PRODUCTION_SYSTEM",
        )
        for marker in required:
            self.assertIn(marker, self.text)

    def test_pre_effect_ordering_is_explicit(self):
        self.assertRegex(
            self.text,
            r"state digest.*before.*execute",
        )


    def test_x_copy_fits_platform_limit(self):
        match = re.search(
            r"## X copy\n\n(.*?)\n\n## Claim audit",
            self.text,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        self.assertLessEqual(len(match.group(1).strip()), 280)

    def test_publication_is_not_claimed(self):
        self.assertIn("Publishing state: NOT_PUBLISHED", self.text)

if __name__ == "__main__":
    unittest.main()
