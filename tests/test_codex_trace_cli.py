import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from verifiable_agent_control_plane.codex_runtime_trace import TraceVerdict, verify_runtime_trace
from verifiable_agent_control_plane.codex_trace_cli import main


class CodexTraceCliTests(unittest.TestCase):
    def _run(self, lines, session_id="s1"):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "trace.jsonl"
            path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main([str(path), "--session-id", session_id])
            return code, json.loads(out.getvalue())

    def test_cli_pass_returns_zero_and_machine_readable_report(self):
        code, payload = self._run([
            json.dumps({"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True}),
            json.dumps({"type": "ExecCommandEnd", "turn_id": "t1", "call_id": "c1", "process_id": "42", "exit_code": 0}),
        ])
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "pass")
        self.assertEqual(payload["receipt_count"], 1)
        self.assertTrue(payload["source_sha"])

    def test_cli_unknown_returns_two(self):
        code, payload = self._run([
            json.dumps({"type": "ToolFinish", "turn_id": "t1", "call_id": "c1", "kind": "completed", "completed_success": True}),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(payload["verdict"], "unknown")
        self.assertEqual(payload["unknown_keys"], [["t1", "c1"]])

    def test_cli_mismatch_returns_three_for_bad_json(self):
        code, payload = self._run(['{"type":'])
        self.assertEqual(code, 3)
        self.assertEqual(payload["verdict"], "mismatch")
        self.assertTrue(payload["errors"])

    def test_non_object_event_is_mismatch_not_exception(self):
        report = verify_runtime_trace([["not", "an", "object"]], session_id="s1")
        self.assertIs(report.verdict, TraceVerdict.MISMATCH)
        self.assertTrue(report.errors)


if __name__ == "__main__":
    unittest.main()
