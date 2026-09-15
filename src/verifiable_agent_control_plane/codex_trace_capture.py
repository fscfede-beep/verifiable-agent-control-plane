from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureReport:
    exit_code: int
    codex_version: str
    stdout_line_count: int
    stderr_line_count: int
    stdout_sha256: str
    stderr_sha256: str
    argv: tuple[str, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture_codex_trace(
    *,
    codex_executable: str,
    output_dir: Path,
    prompt: str,
    cwd: Path,
    timeout_seconds: int = 120,
) -> CaptureReport:
    output_dir = Path(output_dir)
    cwd = Path(cwd)
    output_dir.mkdir(parents=True, exist_ok=True)

    version = subprocess.run(
        [codex_executable, "--version"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    ).stdout.strip()

    argv = (
        codex_executable,
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "-s",
        "read-only",
        "-a",
        "never",
        "-C",
        str(cwd),
        prompt,
    )
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    stdout = completed.stdout.encode("utf-8")
    stderr = completed.stderr.encode("utf-8")
    (output_dir / "trace.raw.jsonl").write_bytes(stdout)
    (output_dir / "trace.stderr.txt").write_bytes(stderr)

    report = CaptureReport(
        exit_code=completed.returncode,
        codex_version=version,
        stdout_line_count=len(completed.stdout.splitlines()),
        stderr_line_count=len(completed.stderr.splitlines()),
        stdout_sha256=_sha256(stdout),
        stderr_sha256=_sha256(stderr),
        argv=argv[:-1] + ("<PROMPT_REDACTED>",),
    )
    metadata = asdict(report)
    metadata["argv"] = list(report.argv)
    metadata["prompt_sha256"] = _sha256(prompt.encode("utf-8"))
    (output_dir / "capture.metadata.json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
