#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    return (p.stdout or p.stderr).strip()

def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    p = argparse.ArgumentParser(description="Collect a sanitized RUMBO Twin environment attestation.")
    p.add_argument("--role", choices=("primary", "twin"), required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tests-result", choices=("PASS", "FAIL"), required=True,
                    help="Run the test suite separately and pass its final result.")
    a = p.parse_args()
    report = {
        "schema":"rumbo-twin-attestation/v2",
        "environment_role":a.role,
        "environment_id":a.id,
        "repository":"fscfede-beep/verifiable-agent-control-plane",
        "branch":run("git","branch","--show-current"),
        "commit":run("git","rev-parse","HEAD"),
        "python":platform.python_version(),
        "platform":platform.platform(),
        "ag_file_sha256":sha(ROOT/"AGENTS.md"),
        "integration_registry_sha256":sha(ROOT/"twin/integration-registry.yaml"),
        "memory_policy_sha256":sha(ROOT/"twin/MEMORY_POLICY.md"),
        "tests_command":"python -m unittest discover -s tests -v",
        "tests":a.tests_result,
    }
    Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
