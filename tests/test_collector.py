import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCollector(unittest.TestCase):
    def test_collector_derives_pass_from_real_suite(self):
        # Avoid recursive collector -> unittest -> test_collector -> collector execution.
        if os.getenv("RUMBO_TWIN_ATTESTATION_RUN") == "1":
            self.skipTest("collector integration test is outside the attestation suite")

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "a.json"
            env = os.environ.copy()
            env["RUMBO_TWIN_ATTESTATION_RUN"] = "1"
            r = subprocess.run(
                [
                    sys.executable,
                    "twin/collect_attestation.py",
                    "--role",
                    "primary",
                    "--id",
                    "A",
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            d = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(d["schema"], "rumbo-twin-attestation/v4")
            self.assertEqual(d["tests"], "PASS")
            self.assertTrue(d["working_tree_clean"])
            self.assertEqual(d["environment_role"], "primary")
            self.assertEqual(d["environment_id"], "A")
            self.assertIn("commit", d)
            self.assertIn("twin_spec_digest", d)
            self.assertIn("tool_policy_digest", d)

    def test_collector_requires_an_environment_id(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "a.json"
            r = subprocess.run(
                [
                    sys.executable,
                    "twin/collect_attestation.py",
                    "--role",
                    "primary",
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
