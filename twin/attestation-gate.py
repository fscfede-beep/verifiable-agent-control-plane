#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = (
    "commit",
    "python",
    "twin_bridge_sha256",
    "twin_config_sha256",
    "tests",
)

def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data

def main() -> int:
    p = argparse.ArgumentParser(description="Fail-closed A/B twin attestation gate")
    p.add_argument("a", type=Path)
    p.add_argument("b", type=Path)
    args = p.parse_args()

    a = load(args.a)
    b = load(args.b)

    missing = {
        role: [k for k in REQUIRED if k not in data]
        for role, data in (("A", a), ("B", b))
    }
    missing = {k: v for k, v in missing.items() if v}
    if missing:
        print(json.dumps({"result": "FAIL-CLOSED", "reason": "missing_fields", "missing": missing}, indent=2))
        return 2

    mismatches = {
        k: {"A": a[k], "B": b[k]}
        for k in REQUIRED
        if a[k] != b[k]
    }

    # Environment identity is allowed to differ. Everything in REQUIRED must match
    # for functional equivalence.
    result = "PASS" if not mismatches else "FAIL-CLOSED"
    print(json.dumps({
        "result": result,
        "checked": list(REQUIRED),
        "mismatches": mismatches,
        "environment_ids": {
            "A": a.get("environment_id"),
            "B": b.get("environment_id"),
        },
    }, indent=2, ensure_ascii=False))
    return 0 if result == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
