#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

REQUIRED=("repository","commit","python","platform","ag_file_sha256","integration_registry_sha256","memory_policy_sha256","working_tree_clean","tests")
REPO="fscfede-beep/verifiable-agent-control-plane"

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b"); args=ap.parse_args()
    a,b=load(args.a),load(args.b)
    if any(any(k not in d for k in REQUIRED) for d in (a,b)):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"missing_fields"},indent=2)); return 2
    if any(d["repository"]!=REPO for d in (a,b)):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"unexpected_repository"},indent=2)); return 2
    roles={"A":a.get("environment_role"),"B":b.get("environment_role")}
    if roles["A"]!="primary" or roles["B"]!="twin":
        print(json.dumps({"result":"FAIL-CLOSED","reason":"invalid_environment_role","roles":roles},indent=2)); return 2
    if any(d["tests"]!="PASS" for d in (a,b)) or any(d["working_tree_clean"] is not True for d in (a,b)):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"environment_not_verified"},indent=2)); return 2
    mismatches={k:{"A":a[k],"B":b[k]} for k in REQUIRED if a[k]!=b[k]}
    result="PASS" if not mismatches else "FAIL-CLOSED"
    print(json.dumps({"result":result,"checked":list(REQUIRED),"mismatches":mismatches,"environment_roles":roles,"environment_ids":{"A":a.get("environment_id"),"B":b.get("environment_id")}},ensure_ascii=False,indent=2))
    return 0 if result=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
