from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from .codex_adapter import CodexFinish, CodexOutcomeKind
from .codex_quiescence import CodexExecEnd, CodexUnifiedExecCorrelator, CODEX_SOURCE_SHA
from .execution_integrity import Quiescence, TerminalReceipt, TerminalRegistry


class TraceVerdict(str, Enum):
    PASS = "pass"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuntimeTraceReport:
    verdict: TraceVerdict
    source_sha: str
    event_count: int
    finish_count: int
    receipt_count: int
    unknown_keys: tuple[tuple[str, str], ...]
    errors: tuple[str, ...]
    receipts: tuple[TerminalReceipt, ...]


def verify_runtime_trace(
    events: Iterable[Mapping[str, Any]], *, session_id: str
) -> RuntimeTraceReport:
    """Verify a captured Codex unified-exec lifecycle trace fail-closed.

    PASS requires every observed ToolFinish to have a terminal receipt and every
    such receipt to be host-managed quiescent. Missing lifecycle evidence is
    UNKNOWN. Malformed input or conflicting material facts are MISMATCH.
    """
    registry = TerminalRegistry()
    correlator = CodexUnifiedExecCorrelator(registry, session_id=session_id)
    seen_finish: set[tuple[str, str]] = set()
    seen_exec_end: set[tuple[str, str]] = set()
    errors: list[str] = []
    event_count = 0

    for index, raw in enumerate(events):
        event_count += 1
        try:
            if not isinstance(raw, Mapping):
                raise TypeError("event must be a JSON object")
            event_type = _required_str(raw, "type")
            if event_type == "ToolFinish":
                finish = _parse_finish(raw)
                key = (finish.turn_id, finish.call_id)
                seen_finish.add(key)
                correlator.observe_finish(finish)
            elif event_type == "ExecCommandEnd":
                end = _parse_exec_end(raw)
                key = (end.turn_id, end.call_id)
                seen_exec_end.add(key)
                correlator.observe_exec_end(end)
            else:
                raise ValueError(f"unsupported event type: {event_type}")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"event[{index}]: {exc}")

    receipts: list[TerminalReceipt] = []
    unknown: set[tuple[str, str]] = set()
    for key in sorted(seen_finish):
        receipt = registry.get(session_id, key[0], key[1])
        if receipt is None:
            unknown.add(key)
            continue
        receipts.append(receipt)
        if not registry.verify(receipt) or receipt.quiescence is not Quiescence.QUIESCENT:
            unknown.add(key)

    # An ExecCommandEnd without its ToolFinish cannot establish the terminal
    # contract for that call; preserve it as incomplete evidence.
    unknown.update(seen_exec_end - seen_finish)

    if errors:
        verdict = TraceVerdict.MISMATCH
    elif event_count == 0 or not seen_finish or unknown:
        verdict = TraceVerdict.UNKNOWN
    else:
        verdict = TraceVerdict.PASS

    return RuntimeTraceReport(
        verdict=verdict,
        source_sha=CODEX_SOURCE_SHA,
        event_count=event_count,
        finish_count=len(seen_finish),
        receipt_count=len(receipts),
        unknown_keys=tuple(sorted(unknown)),
        errors=tuple(errors),
        receipts=tuple(receipts),
    )


def _parse_finish(raw: Mapping[str, Any]) -> CodexFinish:
    kind_text = _required_str(raw, "kind")
    try:
        kind = CodexOutcomeKind(kind_text)
    except ValueError as exc:
        raise ValueError(f"unsupported ToolFinish kind: {kind_text}") from exc

    kwargs: dict[str, Any] = {
        "turn_id": _required_str(raw, "turn_id"),
        "call_id": _required_str(raw, "call_id"),
        "kind": kind,
    }
    if kind is CodexOutcomeKind.COMPLETED:
        kwargs["completed_success"] = _required_bool(raw, "completed_success")
    elif kind is CodexOutcomeKind.FAILED:
        kwargs["handler_executed"] = _required_bool(raw, "handler_executed")
    elif kind is CodexOutcomeKind.ABORTED:
        kwargs["start_observed"] = _required_bool(raw, "start_observed")
    return CodexFinish(**kwargs)


def _parse_exec_end(raw: Mapping[str, Any]) -> CodexExecEnd:
    exit_code = raw.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise TypeError("exit_code must be an integer")
    process_id = raw.get("process_id")
    if process_id is not None and not isinstance(process_id, str):
        raise TypeError("process_id must be a string or null")
    return CodexExecEnd(
        turn_id=_required_str(raw, "turn_id"),
        call_id=_required_str(raw, "call_id"),
        process_id=process_id,
        exit_code=exit_code,
    )


def _required_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{key} must be a non-empty string")
    return value


def _required_bool(raw: Mapping[str, Any], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a boolean")
    return value
