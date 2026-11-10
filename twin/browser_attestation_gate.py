#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def fingerprint(report: dict):
    pages = []
    for item in report.get("targets", []):
        pages.append({
            "title": item.get("title",""),
            "scheme": item.get("scheme",""),
            "host": item.get("host",""),
            "path": item.get("path",""),
        })
    return sorted(pages, key=lambda x: (x["host"], x["path"], x["title"]))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    args = p.parse_args()
    a,b=load(args.a),load(args.b)
    if any(x.get("mode") != "READ_ONLY" for x in (a,b)):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"unexpected_mode"}, indent=2)); return 2
    if any(x.get("security",{}).get("email_addresses_redacted") is not True for x in (a,b)):
        print(json.dumps({"result":"FAIL-CLOSED","reason":"privacy_redaction_missing"}, indent=2)); return 2
    fa,fb=fingerprint(a),fingerprint(b)
    result="PASS" if fa==fb else "DRIFT"
    print(json.dumps({"result":result,"A":fa,"B":fb}, ensure_ascii=False, indent=2))
    return 0 if result=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
