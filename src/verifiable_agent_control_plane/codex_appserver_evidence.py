from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class AppServerVerdict(str, Enum):
    UNKNOWN = "UNKNOWN"
    COMMAND_TERMINAL = "COMMAND_TERMINAL"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True)
class AppServerEvidence:
    verdict: AppServerVerdict
    thread_id: str | None = None
    turn_id: str | None = None
    call_id: str | None = None
    process_id: str | None = None
    exit_code: int | None = None
    toolfinish_observed: bool = False
    quiescence_proven: bool = False


def evaluate_appserver_notifications(events: Iterable[dict[str, Any]]) -> AppServerEvidence:
    started: dict[str, Any] | None = None
    completed: dict[str, Any] | None = None
    for event in events:
        if not isinstance(event, dict):
            return AppServerEvidence(AppServerVerdict.MISMATCH)
        method = event.get("method")
        params = event.get("params")
        if method not in {"item/started", "item/completed", "turn/completed"}:
            continue
        if not isinstance(params, dict):
            return AppServerEvidence(AppServerVerdict.MISMATCH)
        if method.startswith("item/"):
            item = params.get("item")
            if not isinstance(item, dict) or item.get("type") != "commandExecution":
                continue
            record = {
                "thread_id": params.get("threadId"),
                "turn_id": params.get("turnId"),
                "call_id": item.get("id"),
                "process_id": item.get("processId"),
                "status": item.get("status"),
                "exit_code": item.get("exitCode"),
            }
            if method == "item/started":
                started = record
            else:
                completed = record

    if completed is None:
        return AppServerEvidence(AppServerVerdict.UNKNOWN)
    required = (completed["thread_id"], completed["turn_id"], completed["call_id"], completed["process_id"])
    if not all(isinstance(value, str) and value.strip() for value in required):
        return AppServerEvidence(AppServerVerdict.UNKNOWN)
    exit_code = completed["exit_code"]
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        return AppServerEvidence(AppServerVerdict.UNKNOWN)
    if completed["status"] not in {"completed", "failed"}:
        return AppServerEvidence(AppServerVerdict.UNKNOWN)
    if started is not None:
        identity = ("thread_id", "turn_id", "call_id", "process_id")
        if any(started[key] != completed[key] for key in identity):
            return AppServerEvidence(AppServerVerdict.MISMATCH)

    return AppServerEvidence(
        verdict=AppServerVerdict.COMMAND_TERMINAL,
        thread_id=completed["thread_id"],
        turn_id=completed["turn_id"],
        call_id=completed["call_id"],
        process_id=completed["process_id"],
        exit_code=exit_code,
        toolfinish_observed=False,
        quiescence_proven=False,
    )
