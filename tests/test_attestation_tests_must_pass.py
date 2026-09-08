import json, subprocess, sys, tempfile, unittest
from pathlib import Path

BASE={"repository":"fscfede-beep/verifiable-agent-control-plane","commit":"abc","python":"3.13","twin_bridge_sha256":"x","twin_config_sha256":"y"}

class TestAttestationTestsMustPass(unittest.TestCase):
    def run_gate(self,a,b):
        with tempfile.TemporaryDirectory() as td:
            pa,pb=Path(td)/"a.json",Path(td)/"b.json"
            pa.write_text(json.dumps(a),encoding="utf-8"); pb.write_text(json.dumps(b),encoding="utf-8")
            return subprocess.run([sys.executable,"twin/attestation-gate.py",str(pa),str(pb)],capture_output=True,text=True)

    def test_both_pass(self):
        a={**BASE,"tests":"PASS","environment_role":"primary","environment_id":"A"}
        b={**BASE,"tests":"PASS","environment_role":"twin","environment_id":"B"}
        self.assertEqual(self.run_gate(a,b).returncode,0)

    def test_both_fail_cannot_pass(self):
        a={**BASE,"tests":"FAIL","environment_role":"primary","environment_id":"A"}
        b={**BASE,"tests":"FAIL","environment_role":"twin","environment_id":"B"}
        r=self.run_gate(a,b)
        self.assertEqual(r.returncode,2)
        self.assertIn("tests_not_pass",r.stdout)

if __name__=="__main__":
    unittest.main()
