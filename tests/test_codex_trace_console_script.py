import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class CodexTraceConsoleScriptTests(unittest.TestCase):
    def test_console_script_is_installed_and_verifies_unknown_trace(self):
        executable = shutil.which("codex-trace-verify")
        self.assertIsNotNone(executable, "codex-trace-verify must be installed by pip install .")

        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "type": "ToolFinish",
                        "turn_id": "turn-1",
                        "call_id": "call-1",
                        "kind": "completed",
                        "completed_success": True,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [executable, str(trace), "--session-id", "session-1"],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "unknown")
        self.assertEqual(payload["unknown_keys"], [["turn-1", "call-1"]])


if __name__ == "__main__":
    unittest.main()
