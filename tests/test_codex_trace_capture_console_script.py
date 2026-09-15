import shutil
import subprocess
import unittest


class CodexTraceCaptureConsoleScriptTests(unittest.TestCase):
    def test_console_script_is_installed_and_has_help(self):
        executable = shutil.which("codex-trace-capture")
        self.assertIsNotNone(executable)
        result = subprocess.run(
            [executable, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--output-dir", result.stdout)
        self.assertIn("--codex", result.stdout)


if __name__ == "__main__":
    unittest.main()
