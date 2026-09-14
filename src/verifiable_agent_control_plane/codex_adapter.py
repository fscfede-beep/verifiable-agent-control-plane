from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .execution_integrity import (
    EffectVerdict,
    ExecutionState,
    Outcome,
    QuiescenceScope,
    TerminalReceipt,
    TerminalRegistry,
)


class CodexOutcomeKind(str, Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class CodexFinish:
    """Lossless facts needed from Codex ToolFinish plus lifecycle observation.

    The shape is pinned to openai/codex main commit
    ea3c4848d8481aa741475a7e29304115c1adb8aa (2026-09-14).
    """

    turn_id: str
    call_id: str
    kind: CodexOutcomeKind
    completed_success: Optional[bool] = None
    handler_executed: Optional[bool] = None
    start_observed: Optional[bool] = None
    managed_writers_alive: Optional[bool] = None


def terminalize_codex_finish(
    registry: TerminalRegistry,
    *,
    session_id: str,
    finish: CodexFinish,
    effect_verdict: EffectVerdict = EffectVerdict.UNKNOWN,
) -> TerminalReceipt:
    execution_state, outcome, writers_alive = _map_finish(finish)
    return registry.terminalize(
        session_id=session_id,
        turn_id=finish.turn_id,
        tool_use_id=finish.call_id,
        execution_state=execution_state,
        outcome=outcome,
        managed_writers_alive=writers_alive,
        quiescence_scope=QuiescenceScope.HOST_MANAGED,
        effect_verdict=effect_verdict,
    )


def _map_finish(finish: CodexFinish) -> tuple[ExecutionState, Outcome, Optional[bool]]:
    if finish.kind is CodexOutcomeKind.BLOCKED:
        return ExecutionState.NOT_STARTED, Outcome.BLOCKED, False

    if finish.kind is CodexOutcomeKind.COMPLETED:
        if finish.completed_success is None:
            raise ValueError("completed_success is required for Codex Completed")
        return ExecutionState.FINISHED, Outcome.COMPLETED, finish.managed_writers_alive

    if finish.kind is CodexOutcomeKind.FAILED:
        if finish.handler_executed is None:
            raise ValueError("handler_executed is required for Codex Failed")
        state = ExecutionState.FINISHED if finish.handler_executed else ExecutionState.NOT_STARTED
        writers_alive = finish.managed_writers_alive if finish.handler_executed else False
        return state, Outcome.FAILED, writers_alive

    if finish.kind is CodexOutcomeKind.ABORTED:
        if finish.start_observed is None:
            raise ValueError("start_observed is required for Codex Aborted")
        state = ExecutionState.FINISHED if finish.start_observed else ExecutionState.NOT_STARTED
        writers_alive = finish.managed_writers_alive if finish.start_observed else False
        return state, Outcome.CANCELLED, writers_alive

    raise ValueError(f"unsupported Codex outcome: {finish.kind}")
