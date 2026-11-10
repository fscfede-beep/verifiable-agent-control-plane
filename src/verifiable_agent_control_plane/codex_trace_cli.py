from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .codex_runtime_trace import TraceVerdict, verify_runtime_trace


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return events, [f"read: {exc}"]

    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {lineno}: event must be a JSON object")
            continue
        events.append(value)
    return events, errors


def _payload(report, loader_errors: list[str]) -> dict[str, Any]:
    errors = [*loader_errors, *report.errors]
    verdict = TraceVerdict.MISMATCH.value if loader_errors else report.verdict.value
    return {
        "verdict": verdict,
        "source_sha": report.source_sha,
        "event_count": report.event_count,
        "finish_count": report.finish_count,
        "receipt_count": report.receipt_count,
        "unknown_keys": [list(key) for key in report.unknown_keys],
        "errors": errors,
        "receipt_sha256": [receipt.receipt_sha256 for receipt in report.receipts],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a normalized Codex unified-exec runtime trace fail-closed."
    )
    parser.add_argument("trace", type=Path, help="Path to normalized JSONL trace")
    parser.add_argument("--session-id", required=True, help="Session identity bound into receipts")
    args = parser.parse_args(argv)

    events, loader_errors = _load_jsonl(args.trace)
    report = verify_runtime_trace(events, session_id=args.session_id)
    payload = _payload(report, loader_errors)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    verdict = payload["verdict"]
    if verdict == TraceVerdict.PASS.value:
        return 0
    if verdict == TraceVerdict.UNKNOWN.value:
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
