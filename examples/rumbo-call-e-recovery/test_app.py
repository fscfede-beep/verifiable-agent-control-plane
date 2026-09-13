import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("app.py")
SPEC = importlib.util.spec_from_file_location("rumbo_calle_app", MODULE_PATH)
app = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = app
assert SPEC.loader is not None
SPEC.loader.exec_module(app)


class RecoveryAgentTests(unittest.TestCase):
    def test_valid_e164(self):
        self.assertEqual(app.validate_e164("+14155550123"), "+14155550123")

    def test_invalid_phone_rejected(self):
        for phone in ["4155550123", "+1 415 555 0123", "+0123", ""]:
            with self.subTest(phone=phone):
                with self.assertRaises(ValueError):
                    app.validate_e164(phone)

    def test_idempotency_is_stable(self):
        a = app.build_plan("+14155550123", workflow_id="lead-123")
        b = app.build_plan("+14155550123", workflow_id="lead-123")
        self.assertEqual(a.idempotency_key, b.idempotency_key)

    def test_different_workflow_changes_idempotency(self):
        a = app.build_plan("+14155550123", workflow_id="lead-123")
        b = app.build_plan("+14155550123", workflow_id="lead-124")
        self.assertNotEqual(a.idempotency_key, b.idempotency_key)

    def test_preview_redacts_phone(self):
        plan = app.build_plan("+14155550123", workflow_id="lead-123")
        preview = app.redacted_preview(plan)
        self.assertNotIn("+14155550123", str(preview))
        self.assertIn("phone_fingerprint", preview)

    def test_schema_is_bounded(self):
        props = app.RECIPIENT_RESULT_SCHEMA["properties"]
        self.assertEqual(
            props["next_action"]["enum"],
            ["human_follow_up", "schedule_callback", "close", "none"],
        )
        self.assertFalse(app.RECIPIENT_RESULT_SCHEMA["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
