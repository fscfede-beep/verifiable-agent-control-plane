import unittest

from verifiable_agent_control_plane.codex_appserver_evidence import (
    AppServerEvidence,
    AppServerVerdict,
    evaluate_appserver_notifications,
)


class CodexAppServerEvidenceTests(unittest.TestCase):
    def test_completed_command_with_real_ids_is_command_terminal_not_quiescent(self):
        events = [
            {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "inProgress", "processId": "p1", "source": "unifiedExecStartup"}}},
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p1", "source": "unifiedExecStartup", "exitCode": 0}}},
            {"method": "turn/completed", "params": {"threadId": "th1", "turnId": "tu1"}},
        ]
        result = evaluate_appserver_notifications(events)
        self.assertEqual(result.verdict, AppServerVerdict.COMMAND_TERMINAL)
        self.assertEqual(result.thread_id, "th1")
        self.assertEqual(result.turn_id, "tu1")
        self.assertEqual(result.call_id, "call1")
        self.assertEqual(result.process_id, "p1")
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.toolfinish_observed)
        self.assertFalse(result.quiescence_proven)

    def test_missing_process_id_is_unknown(self):
        events = [{"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "exitCode": 0}}}]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.UNKNOWN)

    def test_conflicting_identity_is_mismatch(self):
        events = [
            {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "inProgress", "processId": "p1"}}},
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p2", "exitCode": 0}}},
        ]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.MISMATCH)


if __name__ == "__main__":
    unittest.main()
