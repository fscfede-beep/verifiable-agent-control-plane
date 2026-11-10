import ast
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "examples" / "reliable_tool_workflow.py"


def load_example():
    spec = importlib.util.spec_from_file_location("reliable_tool_workflow", EXAMPLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load quickstart example")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReliableToolWorkflowTests(unittest.TestCase):
    def test_verified_transition_reaches_revision_one(self):
        example = load_example()
        next_state, receipt, effect = example.run_verified_transition()

        self.assertEqual(next_state.revision, 1)
        self.assertEqual(next_state.checkpoint, "R1")
        self.assertEqual(dict(effect.observed_payload), {"key": "mode", "value": "safe"})
        self.assertTrue(receipt.verify())

    def test_state_drift_rejection_happens_before_target_mutation(self):
        example = load_example()
        reason, blocked_values = example.run_state_drift_rejection()

        self.assertEqual(reason, "state drift after decision")
        self.assertEqual(blocked_values, {})

    def test_main_reports_pass_and_fail_closed_markers(self):
        example = load_example()
        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer):
            exit_code = example.main()

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("PASS", output)
        self.assertIn("FAIL-CLOSED", output)
        self.assertIn("state drift after decision", output)

    def test_example_uses_only_public_package_imports(self):
        tree = ast.parse(EXAMPLE_PATH.read_text(encoding="utf-8"))
        package_imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("verifiable_agent_control_plane")
        ]
        self.assertEqual(package_imports, ["verifiable_agent_control_plane"])
