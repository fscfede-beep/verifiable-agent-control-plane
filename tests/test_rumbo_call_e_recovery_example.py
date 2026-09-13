import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "examples" / "rumbo-call-e-recovery" / "app.py"
SPEC = importlib.util.spec_from_file_location("rumbo_call_e_recovery_example", APP_PATH)
app = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = app
assert SPEC.loader is not None
SPEC.loader.exec_module(app)


class RumboCallERecoveryExampleTests(unittest.TestCase):
    def test_dry_run_redacts_recipient_and_keeps_human_gate(self):
        phone = "+14155550123"
        plan = app.build_plan(phone, workflow_id="ci-demo")
        preview = app.redacted_preview(plan)
        self.assertNotIn(phone, str(preview))
        self.assertFalse(preview["safety"]["api_key_logged"])
        self.assertFalse(preview["safety"]["phone_logged"])
        self.assertEqual(
            preview["safety"]["consequential_action"],
            "human_approval_required",
        )

    def test_idempotency_key_is_stable_for_retry(self):
        first = app.build_plan("+14155550123", workflow_id="ci-demo")
        retry = app.build_plan("+14155550123", workflow_id="ci-demo")
        self.assertEqual(first.idempotency_key, retry.idempotency_key)

    def test_recipient_schema_rejects_unbounded_fields(self):
        self.assertFalse(app.RECIPIENT_RESULT_SCHEMA["additionalProperties"])
        self.assertEqual(
            app.RECIPIENT_RESULT_SCHEMA["properties"]["next_action"]["enum"],
            ["human_follow_up", "schedule_callback", "close", "none"],
        )


if __name__ == "__main__":
    unittest.main()
