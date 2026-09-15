import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from verifiable_agent_control_plane.codex_trace_capture import capture_codex_trace


class CodexTraceCaptureTests(unittest.TestCase):
    def test_capture_preserves_raw_streams_metadata_and_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = root / ("fake-codex.cmd" if os.name == "nt" else "fake-codex")
            if os.name == "nt":
                fake.write_text(
                    "@echo off\r\n"
                    "if \"%1\"==\"--version\" (echo codex-cli 9.9.9& exit /b 0)\r\n"
                    "echo {\"type\":\"thread.started\"}\r\n"
                    "echo diagnostic 1>&2\r\n"
                    "exit /b 7\r\n",
                    encoding="utf-8",
                )
            else:
                fake.write_text(
                    "#!/bin/sh\n"
                    "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli 9.9.9'; exit 0; fi\n"
                    "echo '{\"type\":\"thread.started\"}'\n"
                    "echo diagnostic >&2\n"
                    "exit 7\n",
                    encoding="utf-8",
                )
                fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

            out = root / "capture"
            report = capture_codex_trace(
                codex_executable=str(fake),
                output_dir=out,
                prompt="print RUMBO_TRACE_OK",
                cwd=root,
            )

            self.assertEqual(report.exit_code, 7)
            self.assertEqual(report.codex_version, "codex-cli 9.9.9")
            self.assertEqual(report.stdout_line_count, 1)
            self.assertEqual(report.stderr_line_count, 1)
            self.assertTrue(report.stdout_sha256)
            self.assertTrue(report.stderr_sha256)
            self.assertEqual((out / "trace.raw.jsonl").read_text(encoding="utf-8").strip(), '{"type":"thread.started"}')
            self.assertEqual((out / "trace.stderr.txt").read_text(encoding="utf-8").strip(), "diagnostic")
            metadata = json.loads((out / "capture.metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["exit_code"], 7)
            self.assertEqual(metadata["codex_version"], "codex-cli 9.9.9")
            self.assertIn("--json", metadata["argv"])
            self.assertIn("--ephemeral", metadata["argv"])
            self.assertIn("read-only", metadata["argv"])
            self.assertNotIn("-a", metadata["argv"])
            self.assertNotIn("--ask-for-approval", metadata["argv"])
            self.assertEqual(metadata["observation_surface"], "codex_exec_json")
            self.assertEqual(metadata["unified_exec_coverage"], "NOT_PROVEN")
            self.assertFalse(metadata["sufficient_for_toolfinish_correlation"])
            self.assertIn("41590", metadata["coverage_basis"])


if __name__ == "__main__":
    unittest.main()
