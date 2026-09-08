import json, subprocess, sys, tempfile
from pathlib import Path
import unittest

class TestCollector(unittest.TestCase):
    def test_collector_is_fast_and_uses_explicit_test_result(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"a.json"
            r=subprocess.run([
                sys.executable,"twin/collect_attestation.py",
                "--role","primary","--id","A","--out",str(out),
                "--tests-result","PASS"
            ],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            d=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(d["schema"],"rumbo-twin-attestation/v2")
            self.assertEqual(d["tests"],"PASS")
            self.assertEqual(d["environment_role"],"primary")
            self.assertEqual(d["environment_id"],"A")

    def test_tests_result_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"a.json"
            r=subprocess.run([
                sys.executable,"twin/collect_attestation.py",
                "--role","primary","--id","A","--out",str(out)
            ],capture_output=True,text=True,timeout=10)
            self.assertNotEqual(r.returncode,0)

if __name__=="__main__":
    unittest.main()
