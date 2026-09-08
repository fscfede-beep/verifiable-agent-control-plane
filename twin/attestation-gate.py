#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_EQUAL=("repository","commit","python","twin_bridge_sha256","twin_config_sha256","tests")
EXPECTED_REPOSITORY="fscfede-beep/verifiable-agent-control-plane"

def load(path:Path)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError(f"{path}: expected JSON object")
    return data

def main()->int:
    p=argparse.ArgumentParser(description="Fail-closed A/B twin attestation gate")
    p.add_argument("a",type=Path); p.add_argument("b",type=Path); args=p.parse_args()
    a,b=load(args.a),load(args.b)

    missing={role:[k for k in REQUIRED_EQUAL if k not in data] for role,data in (("A",a),("B",b))}
    missing={k:v for k,v in missing.items() if v}
    if missing:
        print(json.dumps({"result":"FAIL-CLOSED","reason":"missing_fields","missing":missing},ensure_ascii=False,indent=2)); return 2

    invalid_repo={role:data["repository"] for role,data in (("A",a),("B",b)) if data["repository"]!=EXPECTED_REPOSITORY}
    if invalid_repo:
        print(json.dumps({"result":"FAIL-CLOSED","reason":"unexpected_repository","repositories":invalid_repo},ensure_ascii=False,indent=2)); return 2

    roles={"A":a.get("environment_role"),"B":b.get("environment_role")}
    ids={"A":a.get("environment_id"),"B":b.get("environment_id")}
    if roles["A"] not in (None,"primary") or roles["B"] not in (None,"twin"):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"invalid_environment_role","roles":roles},ensure_ascii=False,indent=2)); return 2

    failed_tests={role:data["tests"] for role,data in (("A",a),("B",b)) if data["tests"]!="PASS"}
    if failed_tests:
        print(json.dumps({"result":"FAIL-CLOSED","reason":"tests_not_pass","tests":failed_tests},ensure_ascii=False,indent=2)); return 2

    mismatches={k:{"A":a[k],"B":b[k]} for k in REQUIRED_EQUAL if a[k]!=b[k]}
    result="PASS" if not mismatches else "FAIL-CLOSED"
    print(json.dumps({"result":result,"checked":list(REQUIRED_EQUAL),"mismatches":mismatches,"environment_roles":roles,"environment_ids":ids},ensure_ascii=False,indent=2))
    return 0 if result=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
