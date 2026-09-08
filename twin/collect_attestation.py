#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORY = "fscfede-beep/verifiable-agent-control-plane"


def run(*cmd: str) -> tuple[str, int]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    return (p.stdout or p.stderr).strip(), p.returncode


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def collect_test_result() -> tuple[str, str, int]:
    output, code = run("python", "-m", "unittest", "discover", "-s", "tests", "-v")
    return ("PASS" if code == 0 else "FAIL", output, code)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Collect a test-derived, bounded RUMBO Twin attestation."
    )
    p.add_argument("--role", choices=("primary", "twin"), required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    remote, remote_code = run("git", "config", "--get", "remote.origin.url")
    status, status_code = run("git", "status", "--porcelain")
    commit, commit_code = run("git", "rev-parse", "HEAD")
    branch, branch_code = run("git", "branch", "--show-current")

    normalized_remote = remote.strip().removesuffix(".git")
    canonical_remotes = {
        f"https://github.com/{EXPECTED_REPOSITORY}",
        f"git@github.com:{EXPECTED_REPOSITORY}",
        EXPECTED_REPOSITORY,
    }
    if remote_code != 0 or normalized_remote not in canonical_remotes:
        print("FAIL-CLOSED: origin is not the canonical repository")
        return 2
    if status_code != 0 or status:
        print("FAIL-CLOSED: working tree is dirty")
        return 2
    if commit_code != 0 or branch_code != 0:
        print("FAIL-CLOSED: unable to determine repository revision")
        return 2

    tests, test_output, test_code = collect_test_result()
    if test_code != 0:
        print(test_output)
        print("FAIL-CLOSED: test suite did not pass; no attestation written")
        return test_code

    report = {
        "schema": "rumbo-twin-attestation/v4",
        "environment_role": args.role,
        "environment_id": args.id,
        "repository": EXPECTED_REPOSITORY,
        "branch": branch,
        "commit": commit,
        "python": platform.python_version(),
        "runtime_version": platform.python_version(),
        "platform": platform.platform(),
        "twin_spec_digest": sha(ROOT / "twin/environment-bridge.yaml"),
        "tool_policy_digest": sha(ROOT / "twin/integration-registry.yaml"),
        "twin_bridge_sha256": sha(ROOT / "twin/ENVIRONMENT_BRIDGE.md"),
        "ag_file_sha256": sha(ROOT / "AGENTS.md"),
        "integration_registry_sha256": sha(ROOT / "twin/integration-registry.yaml"),
        "memory_policy_sha256": sha(ROOT / "twin/MEMORY_POLICY.md"),
        "working_tree_clean": True,
        "tests_command": "python -m unittest discover -s tests -v",
        "tests": tests,
    }
    Path(args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
