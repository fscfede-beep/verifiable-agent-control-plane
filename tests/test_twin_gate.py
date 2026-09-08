from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "twin" / "attestation-gate.py"


def report(role: str, *, commit: str = "abc", tests: str = "PASS") -> dict:
    return {
        "schema": "rumbo-twin-attestation/v4",
        "environment_role": role,
        "environment_id": role,
        "repository": "fscfede-beep/verifiable-agent-control-plane",
        "branch": "main",
        "commit": commit,
        "python": "3.13.0",
        "runtime_version": "3.13.0",
        "platform": "test-platform",
        "twin_spec_digest": "spec",
        "tool_policy_digest": "policy",
        "twin_bridge_sha256": "bridge",
        "ag_file_sha256": "ag",
        "integration_registry_sha256": "registry",
        "memory_policy_sha256": "memory",
        "working_tree_clean": True,
        "tests_command": "python -m unittest discover -s tests -v",
        "tests": tests,
    }


def run_gate(tmp_path: Path, a: dict, b: dict) -> subprocess.CompletedProcess[str]:
    a_path = tmp_path / "A.json"
    b_path = tmp_path / "B.json"
    a_path.write_text(json.dumps(a), encoding="utf-8")
    b_path.write_text(json.dumps(b), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(GATE), str(a_path), str(b_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_gate_passes_only_for_matching_test_derived_reports(tmp_path: Path) -> None:
    result = run_gate(tmp_path, report("primary"), report("twin"))
    assert result.returncode == 0
    assert '"result": "PASS"' in result.stdout


def test_gate_fails_closed_for_test_failure(tmp_path: Path) -> None:
    result = run_gate(tmp_path, report("primary"), report("twin", tests="FAIL"))
    assert result.returncode != 0
    assert "environment_not_verified" in result.stdout


def test_gate_fails_closed_for_revision_mismatch(tmp_path: Path) -> None:
    result = run_gate(tmp_path, report("primary"), report("twin", commit="different"))
    assert result.returncode != 0
    assert "mismatches" in result.stdout
