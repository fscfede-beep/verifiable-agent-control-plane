#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = (
    "schema",
    "repository",
    "commit",
    "python",
    "platform",
    "twin_spec_digest",
    "tool_policy_digest",
    "ag_file_sha256",
    "integration_registry_sha256",
    "memory_policy_sha256",
    "working_tree_clean",
    "tests",
)
REPO = "fscfede-beep/verifiable-agent-control-plane"
SCHEMA = "rumbo-twin-attestation/v4"


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed A/B Twin attestation gate.")
    ap.add_argument("a")
    ap.add_argument("b")
    args = ap.parse_args()

    try:
        a, b = load(args.a), load(args.b)
    except Exception as exc:
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "invalid_json", "error": str(exc)}))
        return 2

    reports = {"A": a, "B": b}
    missing = {
        role: [key for key in REQUIRED if key not in report]
        for role, report in reports.items()
    }
    if any(missing.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "missing_fields", "missing": missing}, indent=2))
        return 2

    if any(report["schema"] != SCHEMA for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "unsupported_schema"}, indent=2))
        return 2
    if any(report["repository"] != REPO for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "unexpected_repository"}, indent=2))
        return 2

    roles = {"A": a.get("environment_role"), "B": b.get("environment_role")}
    if roles != {"A": "primary", "B": "twin"}:
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "invalid_environment_role", "roles": roles}, indent=2))
        return 2

    if any(report["tests"] != "PASS" or report["working_tree_clean"] is not True for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "environment_not_verified"}, indent=2))
        return 2

    checked = tuple(key for key in REQUIRED if key != "schema")
    mismatches = {key: {"A": a[key], "B": b[key]} for key in checked if a[key] != b[key]}

    result = "PASS" if not mismatches else "FAIL-CLOSED"
    payload = {
        "result": result,
        "checked": list(checked),
        "mismatches": mismatches,
        "environment_roles": roles,
        "environment_ids": {"A": a["environment_id"], "B": b["environment_id"]},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
