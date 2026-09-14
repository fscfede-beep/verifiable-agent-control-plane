from __future__ import annotations

from dataclasses import dataclass, asdict
from copy import deepcopy
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Optional


class ExecutionState(str, Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    FINISHED = "finished"


class Outcome(str, Enum):
    UNKNOWN = "unknown"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Quiescence(str, Enum):
    UNKNOWN = "unknown"
    NOT_QUIESCENT = "not_quiescent"
    QUIESCENT = "quiescent"


class QuiescenceScope(str, Enum):
    HOST_MANAGED = "host_managed"
    DECLARED_EXTERNAL = "declared_external"
    UNKNOWN = "unknown"


class EffectVerdict(str, Enum):
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EffectObservation:
    expected: Mapping[str, Any]
    observed: Optional[Mapping[str, Any]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected", deepcopy(self.expected))
        object.__setattr__(self, "observed", deepcopy(self.observed))

    def verdict(self) -> EffectVerdict:
        if self.observed is None:
            return EffectVerdict.UNKNOWN
        if not _deep_equal(self.expected, self.observed):
            return EffectVerdict.MISMATCH
        return EffectVerdict.VERIFIED


@dataclass(frozen=True)
class TerminalReceipt:
    protocol_version: str
    session_id: str
    turn_id: str
    tool_use_id: str
    executed: Optional[bool]
    execution_state: ExecutionState
    outcome: Outcome
    quiescence: Quiescence
    quiescence_scope: QuiescenceScope
    effect_verdict: EffectVerdict
    receipt_sha256: str

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("receipt_sha256")
        for key, value in list(data.items()):
            if isinstance(value, Enum):
                data[key] = value.value
        return data


class TerminalRegistry:
    """Exactly-once terminal receipt registry keyed by composite tool identity."""

    def __init__(self, protocol_version: str = "rei.v1") -> None:
        self.protocol_version = protocol_version
        self._receipts: dict[tuple[str, str, str], TerminalReceipt] = {}

    def terminalize(
        self,
        *,
        session_id: str,
        turn_id: str,
        tool_use_id: str,
        execution_state: ExecutionState,
        outcome: Outcome,
        managed_writers_alive: Optional[bool],
        quiescence_scope: QuiescenceScope = QuiescenceScope.HOST_MANAGED,
        effect_verdict: EffectVerdict = EffectVerdict.UNKNOWN,
    ) -> TerminalReceipt:
        _validate_execution_outcome(execution_state, outcome)
        if not session_id.strip() or not turn_id.strip() or not tool_use_id.strip():
            raise ValueError("session_id, turn_id, and tool_use_id must be non-empty")

        identity = (session_id, turn_id, tool_use_id)
        existing = self._receipts.get(identity)
        if existing is not None:
            candidate_executed = _executed_fact(execution_state, outcome)
            candidate_quiescence = _quiescence_fact(
                execution_state=execution_state,
                managed_writers_alive=managed_writers_alive,
            )
            if (
                existing.execution_state is not execution_state
                or existing.outcome is not outcome
                or existing.executed is not candidate_executed
                or existing.quiescence is not candidate_quiescence
                or existing.quiescence_scope is not quiescence_scope
                or existing.effect_verdict is not effect_verdict
            ):
                raise ValueError(
                    "terminal fact conflict: tool_use_id replay changed material terminal facts"
                )
            return existing

        executed = _executed_fact(execution_state, outcome)
        quiescence = _quiescence_fact(
            execution_state=execution_state,
            managed_writers_alive=managed_writers_alive,
        )
        if effect_verdict is EffectVerdict.VERIFIED and quiescence is not Quiescence.QUIESCENT:
            raise ValueError("verified effect requires quiescence")

        payload = {
            "protocol_version": self.protocol_version,
            "session_id": session_id,
            "turn_id": turn_id,
            "tool_use_id": tool_use_id,
            "executed": executed,
            "execution_state": execution_state.value,
            "outcome": outcome.value,
            "quiescence": quiescence.value,
            "quiescence_scope": quiescence_scope.value,
            "effect_verdict": effect_verdict.value,
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        receipt = TerminalReceipt(
            protocol_version=self.protocol_version,
            session_id=session_id,
            turn_id=turn_id,
            tool_use_id=tool_use_id,
            executed=executed,
            execution_state=execution_state,
            outcome=outcome,
            quiescence=quiescence,
            quiescence_scope=quiescence_scope,
            effect_verdict=effect_verdict,
            receipt_sha256=digest,
        )
        self._receipts[identity] = receipt
        return receipt

    def get(
        self, session_id: str, turn_id: str, tool_use_id: str
    ) -> Optional[TerminalReceipt]:
        return self._receipts.get((session_id, turn_id, tool_use_id))

    def verify(self, receipt: TerminalReceipt) -> bool:
        return self.verify_payload_hash(receipt.payload(), receipt.receipt_sha256)

    @staticmethod
    def verify_payload_hash(payload: Mapping[str, Any], expected_sha256: str) -> bool:
        material = {key: value for key, value in payload.items() if key != "receipt_sha256"}
        actual = hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()
        return actual == expected_sha256

    def __len__(self) -> int:
        return len(self._receipts)


def _validate_execution_outcome(execution_state: ExecutionState, outcome: Outcome) -> None:
    impossible = {
        (ExecutionState.NOT_STARTED, Outcome.COMPLETED),
        (ExecutionState.STARTED, Outcome.BLOCKED),
        (ExecutionState.STARTED, Outcome.COMPLETED),
        (ExecutionState.FINISHED, Outcome.BLOCKED),
    }
    if (execution_state, outcome) in impossible:
        raise ValueError(
            "invalid execution/outcome combination: "
            f"{execution_state.value}/{outcome.value}"
        )


def _executed_fact(execution_state: ExecutionState, outcome: Outcome) -> Optional[bool]:
    if execution_state is ExecutionState.NOT_STARTED:
        return False
    if execution_state in {ExecutionState.STARTED, ExecutionState.FINISHED}:
        return True
    return None


def _quiescence_fact(*, execution_state: ExecutionState, managed_writers_alive: Optional[bool]) -> Quiescence:
    if managed_writers_alive is True:
        return Quiescence.NOT_QUIESCENT
    if managed_writers_alive is None:
        return Quiescence.UNKNOWN
    if execution_state in {ExecutionState.NOT_STARTED, ExecutionState.FINISHED}:
        return Quiescence.QUIESCENT
    return Quiescence.UNKNOWN


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _deep_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left.keys()) != set(right.keys()):
            return False
        return all(_deep_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(
            _deep_equal(l_item, r_item) for l_item, r_item in zip(left, right)
        )
    return left == right
