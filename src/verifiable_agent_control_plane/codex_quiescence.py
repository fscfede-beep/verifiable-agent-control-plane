from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .codex_adapter import CodexFinish, CodexOutcomeKind, terminalize_codex_finish
from .execution_integrity import TerminalReceipt, TerminalRegistry

CODEX_SOURCE_SHA = "ea3c4848d8481aa741475a7e29304115c1adb8aa"


@dataclass(frozen=True)
class CodexExecEnd:
    """Observed unified-exec ExecCommandEnd facts at the pinned Codex source revision."""

    turn_id: str
    call_id: str
    process_id: Optional[str]
    exit_code: int

    def __post_init__(self) -> None:
        if not self.turn_id.strip() or not self.call_id.strip():
            raise ValueError("turn_id and call_id must be non-empty")


class CodexUnifiedExecCorrelator:
    """Correlate ToolFinish with unified-exec termination evidence.

    Correlation key is (turn_id, call_id). A correlated ExecCommandEnd only
    proves HOST_MANAGED quiescence when exit_code != -1 at CODEX_SOURCE_SHA.
    """

    def __init__(self, registry: TerminalRegistry, *, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id must be non-empty")
        self.registry = registry
        self.session_id = session_id
        self._pending: dict[tuple[str, str], CodexFinish] = {}
        self._exec_ends: dict[tuple[str, str], CodexExecEnd] = {}

    def observe_finish(self, finish: CodexFinish) -> Optional[TerminalReceipt]:
        key = (finish.turn_id, finish.call_id)
        existing = self._pending.get(key)
        if existing is not None and existing != finish:
            raise ValueError("ToolFinish conflict for the same turn_id/call_id")

        if self._does_not_require_exec_end(finish):
            return terminalize_codex_finish(
                self.registry,
                session_id=self.session_id,
                finish=finish,
            )

        self._pending[key] = finish
        if key in self._exec_ends:
            return self._terminalize_from_exec_end(key)
        return None

    def observe_exec_end(self, event: CodexExecEnd) -> Optional[TerminalReceipt]:
        key = (event.turn_id, event.call_id)
        existing = self._exec_ends.get(key)
        if existing is not None:
            if existing != event:
                raise ValueError("ExecCommandEnd conflict for the same turn_id/call_id")
            return self.registry.get(self.session_id, event.turn_id, event.call_id)

        self._exec_ends[key] = event
        if key in self._pending:
            return self._terminalize_from_exec_end(key)
        return None

    def finalize_unknown(self, *, turn_id: str, call_id: str) -> TerminalReceipt:
        key = (turn_id, call_id)
        finish = self._pending.pop(key, None)
        if finish is None:
            existing = self.registry.get(self.session_id, turn_id, call_id)
            if existing is not None:
                return existing
            raise KeyError("no pending ToolFinish for turn_id/call_id")

        return terminalize_codex_finish(
            self.registry,
            session_id=self.session_id,
            finish=finish,
        )

    def _terminalize_from_exec_end(self, key: tuple[str, str]) -> TerminalReceipt:
        finish = self._pending.pop(key)
        event = self._exec_ends[key]
        writers_alive = False if event.exit_code != -1 else None
        observed_finish = CodexFinish(
            turn_id=finish.turn_id,
            call_id=finish.call_id,
            kind=finish.kind,
            completed_success=finish.completed_success,
            handler_executed=finish.handler_executed,
            start_observed=finish.start_observed,
            managed_writers_alive=writers_alive,
        )
        return terminalize_codex_finish(
            self.registry,
            session_id=self.session_id,
            finish=observed_finish,
        )

    @staticmethod
    def _does_not_require_exec_end(finish: CodexFinish) -> bool:
        if finish.kind is CodexOutcomeKind.BLOCKED:
            return True
        if finish.kind is CodexOutcomeKind.FAILED and finish.handler_executed is False:
            return True
        if finish.kind is CodexOutcomeKind.ABORTED and finish.start_observed is False:
            return True
        return False
