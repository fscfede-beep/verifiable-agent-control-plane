import unittest

from verifiable_agent_control_plane.codex_appserver_evidence import AppServerVerdict, evaluate_appserver_notifications


class CodexAppServerEvidenceTests(unittest.TestCase):
    def test_completed_unified_exec_command_and_turn_is_turn_terminal_not_quiescent(self):
        events = [
            {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "inProgress", "processId": "p1", "source": "unifiedExecStartup"}}},
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p1", "source": "unifiedExecStartup", "exitCode": 0}}},
            {"method": "turn/completed", "params": {"threadId": "th1", "turnId": "tu1"}},
        ]
        result = evaluate_appserver_notifications(events)
        self.assertEqual(result.verdict, AppServerVerdict.TURN_TERMINAL)
        self.assertEqual(result.source, "unifiedExecStartup")
        self.assertTrue(result.unified_exec_observed)
        self.assertEqual((result.thread_id, result.turn_id, result.call_id, result.process_id), ("th1", "tu1", "call1", "p1"))
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.toolfinish_observed)
        self.assertFalse(result.quiescence_proven)

    def test_command_terminal_without_turn_completion_is_distinct(self):
        events = [{"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p1", "source": "agent", "exitCode": 0}}}]
        result = evaluate_appserver_notifications(events)
        self.assertEqual(result.verdict, AppServerVerdict.COMMAND_TERMINAL)
        self.assertEqual(result.source, "agent")
        self.assertFalse(result.unified_exec_observed)

    def test_missing_process_id_is_unknown(self):
        events = [{"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "exitCode": 0}}}]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.UNKNOWN)

    def test_conflicting_identity_is_mismatch(self):
        events = [
            {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "inProgress", "processId": "p1"}}},
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p2", "exitCode": 0}}},
        ]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.MISMATCH)

    def test_conflicting_source_is_mismatch(self):
        events = [
            {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "inProgress", "processId": "p1", "source": "unifiedExecStartup"}}},
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p1", "source": "agent", "exitCode": 0}}},
        ]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.MISMATCH)

    def test_turn_completed_for_different_turn_is_mismatch(self):
        events = [
            {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "processId": "p1", "exitCode": 0}}},
            {"method": "turn/completed", "params": {"threadId": "th1", "turnId": "tu2"}},
        ]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.MISMATCH)


if __name__ == "__main__":
    unittest.main()
