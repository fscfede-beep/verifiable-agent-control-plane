import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

class TestCollector(unittest.TestCase):
    def test_schema_and_role(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"a.json"
            r=subprocess.run([sys.executable,"twin/collect_attestation.py","--role","primary","--id","A","--out",str(out)],cwd=".",capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            d=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(d["schema"],"rumbo-twin-attestation/v2")
            self.assertEqual(d["environment_role"],"primary")
            self.assertEqual(d["environment_id"],"A")
            self.assertIn("commit",d)

if __name__=="__main__":
    unittest.main()
