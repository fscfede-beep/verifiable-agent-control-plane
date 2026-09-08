import json, subprocess, sys, tempfile
from pathlib import Path

def write(p, s): p.write_text(s, encoding="utf-8")

with tempfile.TemporaryDirectory() as td:
    a=Path(td)/"a.json"; b=Path(td)/"b.json"
    write(a, '''{"repository":"fscfede-beep/verifiable-agent-control-plane","commit":"same","python":"3.13","twin_bridge_sha256":"same","twin_config_sha256":"same","tests":"PASS","environment_id":"A"}'''); write(b, '''{"repository":"fscfede-beep/verifiable-agent-control-plane","commit":"same","python":"3.13","twin_bridge_sha256":"same","twin_config_sha256":"same","tests":"PASS","environment_id":"B"}''')
    r=subprocess.run([sys.executable, "twin/attestation-gate.py", str(a), str(b)], text=True, capture_output=True)
    assert r.returncode == 0, r.stdout+r.stderr
    print("PASS parity")
