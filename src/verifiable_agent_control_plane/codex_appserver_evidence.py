from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class AppServerVerdict(str, Enum):
    UNKNOWN = "UNKNOWN"
    COMMAND_TERMINAL = "COMMAND_TERMINAL"
    TURN_TERMINAL = "TURN_TERMINAL"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True)
class AppServerEvidence:
    verdict: AppServerVerdict
    thread_id: str | None = None
    turn_id: str | None = None
    call_id: str | None = None
    process_id: str | None = None
    exit_code: int | None = None
    source: str | None = None
    unified_exec_observed: bool = False
    toolfinish_observed: bool = False
    quiescence_proven: bool = False


def evaluate_appserver_notifications(events: Iterable[dict[str, Any]]) -> AppServerEvidence:
    started: dict[str, Any] | None = None
    completed: dict[str, Any] | None = None
    completed_turns: set[tuple[str, str]] = set()
    allowed_sources = {"agent", "userShell", "unifiedExecStartup", "unifiedExecInteraction"}
    for event in events:
        if not isinstance(event, dict): return AppServerEvidence(AppServerVerdict.MISMATCH)
        method, params = event.get("method"), event.get("params")
        if method not in {"item/started", "item/completed", "turn/completed"}: continue
        if not isinstance(params, dict): return AppServerEvidence(AppServerVerdict.MISMATCH)
        if method == "turn/completed":
            thread_id, turn_id = params.get("threadId"), params.get("turnId")
            if not (isinstance(thread_id, str) and thread_id.strip() and isinstance(turn_id, str) and turn_id.strip()): return AppServerEvidence(AppServerVerdict.MISMATCH)
            completed_turns.add((thread_id, turn_id)); continue
        item = params.get("item")
        if not isinstance(item, dict) or item.get("type") != "commandExecution": continue
        record = {
            "thread_id": params.get("threadId"), "turn_id": params.get("turnId"), "call_id": item.get("id"),
            "process_id": item.get("processId"), "status": item.get("status"), "exit_code": item.get("exitCode"),
            "source": item.get("source", "agent"),
        }
        if method == "item/started": started = record
        else: completed = record

    if completed is None: return AppServerEvidence(AppServerVerdict.UNKNOWN)
    required = (completed["thread_id"], completed["turn_id"], completed["call_id"], completed["process_id"])
    if not all(isinstance(value, str) and value.strip() for value in required): return AppServerEvidence(AppServerVerdict.UNKNOWN)
    source = completed["source"] if isinstance(completed["source"], str) else None
    if source not in allowed_sources: return AppServerEvidence(AppServerVerdict.UNKNOWN)
    exit_code = completed["exit_code"]
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or completed["status"] not in {"completed", "failed"}: return AppServerEvidence(AppServerVerdict.UNKNOWN)
    if started is not None and any(started[key] != completed[key] for key in ("thread_id", "turn_id", "call_id", "process_id", "source")): return AppServerEvidence(AppServerVerdict.MISMATCH)
    command_identity = (completed["thread_id"], completed["turn_id"])
    if completed_turns and command_identity not in completed_turns: return AppServerEvidence(AppServerVerdict.MISMATCH)
    verdict = AppServerVerdict.TURN_TERMINAL if command_identity in completed_turns else AppServerVerdict.COMMAND_TERMINAL
    return AppServerEvidence(
        verdict=verdict, thread_id=completed["thread_id"], turn_id=completed["turn_id"], call_id=completed["call_id"],
        process_id=completed["process_id"], exit_code=exit_code, source=source,
        unified_exec_observed=source in {"unifiedExecStartup", "unifiedExecInteraction"}, toolfinish_observed=False, quiescence_proven=False,
    )
