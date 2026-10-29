#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED = (
    "schema",
    "environment_role",
    "environment_id",
    "repository",
    "branch",
    "commit",
    "python",
    "runtime_version",
    "platform",
    "twin_spec_digest",
    "tool_policy_digest",
    "twin_bridge_sha256",
    "ag_file_sha256",
    "integration_registry_sha256",
    "memory_policy_sha256",
    "working_tree_clean",
    "tests_command",
    "tests",
)
REPO = "fscfede-beep/verifiable-agent-control-plane"
SCHEMA = "rumbo-twin-attestation/v4"
PYTHON_PIN = "3.13.17"
TEST_COMMAND = "python -m unittest discover -s tests -v"
DIGEST_FIELDS = (
    "twin_spec_digest", "tool_policy_digest", "twin_bridge_sha256",
    "ag_file_sha256", "integration_registry_sha256", "memory_policy_sha256",
)

def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate_json_key")
        result[name] = value
    return result

def _invalid_constant(value: str) -> None:
    raise ValueError("nonstandard_json_constant")

def validate_report(report: dict) -> list[str]:
    problems = []
    for name in ("python", "runtime_version"):
        if report[name] != PYTHON_PIN:
            problems.append("unexpected_" + name)
    if report["tests_command"] != TEST_COMMAND:
        problems.append("unexpected_tests_command")
    if type(report["branch"]) is not str or not report["branch"] or not re.fullmatch(r"[A-Za-z0-9_./-]+", report["branch"]) or ".." in report["branch"]:
        problems.append("invalid_branch")
    if type(report["commit"]) is not str or re.fullmatch(r"[a-f0-9]{40}", report["commit"]) is None:
        problems.append("invalid_commit")
    if type(report["platform"]) is not str or not report["platform"].startswith("Linux-"):
        problems.append("invalid_platform")
    for name in DIGEST_FIELDS:
        if type(report[name]) is not str or re.fullmatch(r"[a-f0-9]{64}", report[name]) is None:
            problems.append("invalid_digest:" + name)
    return problems



def load(path: str) -> dict:
    data = Path(path).read_bytes()
    if len(data) > 65536:
        raise ValueError("report_too_large")
    parsed = json.loads(data, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    if not isinstance(parsed, dict):
        raise ValueError("report_not_object")
    return parsed


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

    # v4 defines a closed contract: reject any undeclared claims.
    unexpected = {
        role: sorted(set(report) - set(REQUIRED))
        for role, report in reports.items()
    }
    if any(unexpected.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "unexpected_fields", "fields": unexpected}, indent=2))
        return 2

    if any(report["schema"] != SCHEMA for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "unsupported_schema"}, indent=2))
        return 2
    if any(report["repository"] != REPO for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "unexpected_repository"}, indent=2))
        return 2

    contract = {name: validate_report(report) for name, report in reports.items()}
    if any(contract.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "invalid_contract", "problems": contract}, indent=2))
        return 2

    roles = {"A": a.get("environment_role"), "B": b.get("environment_role")}
    if roles != {"A": "primary", "B": "twin"}:
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "invalid_environment_role", "roles": roles}, indent=2))
        return 2

    ids = {"A": a.get("environment_id"), "B": b.get("environment_id")}
    if ids != {"A": "A", "B": "B"}:
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "invalid_environment_id", "ids": ids}, indent=2))
        return 2

    if any(report["tests"] != "PASS" or report["working_tree_clean"] is not True for report in reports.values()):
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "environment_not_verified"}, indent=2))
        return 2

    checked = tuple(key for key in REQUIRED if key not in ("schema", "environment_role", "environment_id"))
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
