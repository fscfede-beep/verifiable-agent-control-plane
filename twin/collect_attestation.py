#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORY="fscfede-beep/verifiable-agent-control-plane"

def run(*cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=False)
    return (p.stdout or p.stderr).strip(), p.returncode

def sha(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    p=argparse.ArgumentParser(description="Collect a bounded, sanitized RUMBO Twin attestation.")
    p.add_argument("--role",choices=("primary","twin"),required=True)
    p.add_argument("--id",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--tests-result",choices=("PASS","FAIL"),required=True)
    a=p.parse_args()

    remote,_=run("git","config","--get","remote.origin.url")
    clean,clean_code=run("git","status","--porcelain")
    commit,_=run("git","rev-parse","HEAD")
    branch,_=run("git","branch","--show-current")

    normalized_remote=remote.strip().removesuffix(".git")
    if normalized_remote not in (
        "https://github.com/"+EXPECTED_REPOSITORY,
        "git@github.com:"+EXPECTED_REPOSITORY,
        EXPECTED_REPOSITORY,
    ):
        raise SystemExit("FAIL-CLOSED: origin is not the canonical repository")
    if clean:
        raise SystemExit("FAIL-CLOSED: working tree is dirty")

    report={
      "schema":"rumbo-twin-attestation/v3",
      "environment_role":a.role,
      "environment_id":a.id,
      "repository":EXPECTED_REPOSITORY,
      "branch":branch,
      "commit":commit,
      "python":platform.python_version(),
      "platform":platform.platform(),
      "ag_file_sha256":sha(ROOT/"AGENTS.md"),
      "integration_registry_sha256":sha(ROOT/"twin/integration-registry.yaml"),
      "memory_policy_sha256":sha(ROOT/"twin/MEMORY_POLICY.md"),
      "working_tree_clean":clean_code==0,
      "tests_command":"python -m unittest discover -s tests -v",
      "tests":a.tests_result,
    }
    Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
