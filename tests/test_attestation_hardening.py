import json, subprocess, sys, tempfile
from pathlib import Path
import unittest

BASE={"repository":"fscfede-beep/verifiable-agent-control-plane","commit":"abc","python":"3.13","twin_bridge_sha256":"x","twin_config_sha256":"y","tests":"PASS"}

class TestAttestationHardening(unittest.TestCase):
    def run_gate(self,a,b):
        with tempfile.TemporaryDirectory() as td:
            pa,pb=Path(td)/"a.json",Path(td)/"b.json"
            pa.write_text(json.dumps(a),encoding="utf-8"); pb.write_text(json.dumps(b),encoding="utf-8")
            return subprocess.run([sys.executable,"twin/attestation-gate.py",str(pa),str(pb)],capture_output=True,text=True)

    def test_pass_for_matching_required_state(self):
        a={**BASE,"environment_role":"primary","environment_id":"A"}
        b={**BASE,"environment_role":"twin","environment_id":"B"}
        r=self.run_gate(a,b)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_fail_for_repository_drift(self):
        a={**BASE,"environment_role":"primary"}
        b={**BASE,"repository":"other/repo","environment_role":"twin"}
        r=self.run_gate(a,b)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("unexpected_repository",r.stdout)

    def test_fail_for_required_drift(self):
        a={**BASE,"environment_role":"primary"}
        b={**BASE,"commit":"def","environment_role":"twin"}
        r=self.run_gate(a,b)
        self.assertEqual(r.returncode,1)
        self.assertIn("FAIL-CLOSED",r.stdout)

if __name__=="__main__":
    unittest.main()
