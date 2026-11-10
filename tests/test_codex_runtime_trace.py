import unittest

from verifiable_agent_control_plane.codex_runtime_trace import (
    TraceVerdict,
    verify_runtime_trace,
)


class CodexRuntimeTraceTests(unittest.TestCase):
    def test_completed_unified_exec_with_confirmed_exit_passes(self):
        report = verify_runtime_trace([
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True},
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": 0},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.PASS)
        self.assertEqual(report.receipt_count, 1)
        self.assertEqual(report.unknown_keys, ())

    def test_missing_exec_end_is_unknown_not_pass(self):
        report = verify_runtime_trace([
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.UNKNOWN)
        self.assertEqual(report.unknown_keys, (("t1", "c1"),))

    def test_unknown_exit_code_is_unknown(self):
        report = verify_runtime_trace([
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True},
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": -1},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.UNKNOWN)
        self.assertEqual(report.receipt_count, 1)

    def test_blocked_before_execution_passes_without_exec_end(self):
        report = verify_runtime_trace([
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "blocked"},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.PASS)
        self.assertEqual(report.receipt_count, 1)

    def test_conflicting_exec_end_is_mismatch(self):
        report = verify_runtime_trace([
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": 0},
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "43", "exit_code": 0},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.MISMATCH)
        self.assertTrue(report.errors)

    def test_malformed_or_unknown_event_is_mismatch(self):
        report = verify_runtime_trace([
            {"type": "SomethingElse", "turn_id": "t1", "call_id": "c1"},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.MISMATCH)

    def test_out_of_order_trace_passes(self):
        report = verify_runtime_trace([
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": 0},
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.PASS)

    def test_empty_trace_is_unknown(self):
        report = verify_runtime_trace([], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.UNKNOWN)


class CodexRuntimeTraceStrictInputTests(unittest.TestCase):
    def test_bool_exit_code_is_rejected(self):
        report = verify_runtime_trace([
            {"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": True},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.MISMATCH)

    def test_conflicting_tool_finish_is_mismatch(self):
        report = verify_runtime_trace([
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True},
            {"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "failed", "handler_executed": True},
        ], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.MISMATCH)


if __name__ == "__main__":
    unittest.main()
