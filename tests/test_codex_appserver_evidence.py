import unittest

from verifiable_agent_control_plane.codex_appserver_evidence import AppServerVerdict, evaluate_appserver_notifications


def completed(call="call1", process="p1", source="agent", status="completed", exit_code=0):
    return {"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": call, "type": "commandExecution", "status": status, "processId": process, "source": source, "exitCode": exit_code}}}


def started(call="call1", process="p1", source="agent"):
    return {"method": "item/started", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": call, "type": "commandExecution", "status": "inProgress", "processId": process, "source": source}}}


class CodexAppServerEvidenceTests(unittest.TestCase):
    def test_completed_unified_exec_command_and_turn_is_turn_terminal_not_quiescent(self):
        events = [started(source="unifiedExecStartup"), completed(source="unifiedExecStartup"), {"method": "turn/completed", "params": {"threadId": "th1", "turnId": "tu1"}}]
        result = evaluate_appserver_notifications(events)
        self.assertEqual(result.verdict, AppServerVerdict.TURN_TERMINAL)
        self.assertEqual(result.source, "unifiedExecStartup")
        self.assertTrue(result.unified_exec_observed)
        self.assertEqual((result.thread_id, result.turn_id, result.call_id, result.process_id), ("th1", "tu1", "call1", "p1"))
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.toolfinish_observed)
        self.assertFalse(result.quiescence_proven)

    def test_distinct_second_start_is_mismatch(self):
        self.assertEqual(evaluate_appserver_notifications([started(), started(call="call2", process="p2"), completed()]).verdict, AppServerVerdict.MISMATCH)

    def test_identical_completed_replay_is_idempotent(self):
        event = completed()
        self.assertEqual(evaluate_appserver_notifications([event, event]).verdict, AppServerVerdict.COMMAND_TERMINAL)

    def test_divergent_or_distinct_second_completion_is_mismatch(self):
        self.assertEqual(evaluate_appserver_notifications([completed(), completed(call="call2", process="p2")]).verdict, AppServerVerdict.MISMATCH)
        self.assertEqual(evaluate_appserver_notifications([completed(), completed(exit_code=1, status="failed")]).verdict, AppServerVerdict.MISMATCH)

    def test_terminal_status_exit_code_mismatch_is_mismatch(self):
        self.assertEqual(evaluate_appserver_notifications([completed(status="failed", exit_code=0)]).verdict, AppServerVerdict.MISMATCH)
        self.assertEqual(evaluate_appserver_notifications([completed(status="completed", exit_code=7)]).verdict, AppServerVerdict.MISMATCH)

    def test_command_terminal_without_turn_completion_is_distinct(self):
        self.assertEqual(evaluate_appserver_notifications([completed()]).verdict, AppServerVerdict.COMMAND_TERMINAL)

    def test_unknown_source_or_missing_process_is_unknown(self):
        self.assertEqual(evaluate_appserver_notifications([completed(source="mystery")]).verdict, AppServerVerdict.UNKNOWN)
        missing = [{"method": "item/completed", "params": {"threadId": "th1", "turnId": "tu1", "item": {"id": "call1", "type": "commandExecution", "status": "completed", "exitCode": 0}}}]
        self.assertEqual(evaluate_appserver_notifications(missing).verdict, AppServerVerdict.UNKNOWN)

    def test_conflicting_identity_or_source_is_mismatch(self):
        self.assertEqual(evaluate_appserver_notifications([started(source="unifiedExecStartup"), completed(process="p2", source="unifiedExecStartup")]).verdict, AppServerVerdict.MISMATCH)
        self.assertEqual(evaluate_appserver_notifications([started(source="unifiedExecStartup"), completed(source="agent")]).verdict, AppServerVerdict.MISMATCH)

    def test_turn_completed_for_different_turn_is_mismatch(self):
        events = [completed(), {"method": "turn/completed", "params": {"threadId": "th1", "turnId": "tu2"}}]
        self.assertEqual(evaluate_appserver_notifications(events).verdict, AppServerVerdict.MISMATCH)


if __name__ == "__main__":
    unittest.main()
