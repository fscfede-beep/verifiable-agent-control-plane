from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "STATE_DRIFT_AFTER_DECISION.md"
README = ROOT / "README.md"


class StateDriftDeepDiveDocsTests(unittest.TestCase):
    def test_deep_dive_exists_with_core_claim_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("DECISION_ACCEPTED != EXECUTION_SAFE", text)
        self.assertIn("state drift after decision", text)
        self.assertIn("blocked_target_mutated=False", text)
        self.assertIn("REFERENCE_IMPLEMENTATION != PRODUCTION_SYSTEM", text)

    def test_deep_dive_points_to_executable_demo(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("python examples/reliable_tool_workflow.py", text)
        self.assertIn("run_state_drift_rejection", text)

    def test_readme_links_the_deep_dive(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("## Technical deep dives", text)
        self.assertIn("docs/STATE_DRIFT_AFTER_DECISION.md", text)


if __name__ == "__main__":
    unittest.main()
