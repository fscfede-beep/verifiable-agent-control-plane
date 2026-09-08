from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .canonical import CanonicalProblemState, CanonicalProblemError, BRAND


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_stable(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContinuityEvent:
    problem_id: str
    revision: int
    state_digest: str
    action: str
    previous_event_hash: str | None
    event_hash: str

    @classmethod
    def build(
        cls,
        *,
        state: CanonicalProblemState,
        action: str,
        previous_event_hash: str | None,
    ) -> "ContinuityEvent":
        state.validate()
        if state.brand != BRAND:
            raise CanonicalProblemError("continuity event requires RUMBO IA state")
        base = {
            "problem_id": state.problem_id,
            "revision": state.revision,
            "state_digest": state.digest,
            "action": action,
            "previous_event_hash": previous_event_hash,
        }
        return cls(event_hash=_hash(base), **base)

    def verify(self) -> bool:
        base = {
            "problem_id": self.problem_id,
            "revision": self.revision,
            "state_digest": self.state_digest,
            "action": self.action,
            "previous_event_hash": self.previous_event_hash,
        }
        return self.event_hash == _hash(base)

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "revision": self.revision,
            "state_digest": self.state_digest,
            "action": self.action,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
        }


@dataclass(frozen=True)
class ContinuityLedger:
    events: tuple[ContinuityEvent, ...] = ()

    def append(self, state: CanonicalProblemState, action: str) -> "ContinuityLedger":
        state.validate()
        previous = self.events[-1].event_hash if self.events else None
        event = ContinuityEvent.build(
            state=state,
            action=action,
            previous_event_hash=previous,
        )
        return ContinuityLedger(self.events + (event,))

    def verify(self, state: CanonicalProblemState | None = None) -> None:
        previous: str | None = None
        expected_revision: int | None = None
        for event in self.events:
            if not event.verify():
                raise CanonicalProblemError("continuity ledger event hash mismatch")
            if event.previous_event_hash != previous:
                raise CanonicalProblemError("continuity ledger chain mismatch")
            if expected_revision is not None and event.revision != expected_revision + 1:
                raise CanonicalProblemError("continuity ledger revision gap")
            expected_revision = event.revision
            previous = event.event_hash
        if state is not None:
            state.validate()
            if not self.events:
                raise CanonicalProblemError("continuity ledger is empty")
            last = self.events[-1]
            if last.problem_id != state.problem_id:
                raise CanonicalProblemError("continuity ledger problem mismatch")
            if last.revision != state.revision:
                raise CanonicalProblemError("continuity ledger revision mismatch")
            if last.state_digest != state.digest:
                raise CanonicalProblemError("continuity ledger state digest mismatch")

    def to_json(self) -> str:
        self.verify()
        return _stable({"events": [event.to_dict() for event in self.events]})

    @classmethod
    def from_json(cls, payload: str) -> "ContinuityLedger":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CanonicalProblemError("invalid continuity ledger JSON") from exc
        if not isinstance(data, Mapping) or not isinstance(data.get("events"), list):
            raise CanonicalProblemError("continuity ledger JSON must contain events list")
        events = []
        for item in data["events"]:
            if not isinstance(item, Mapping):
                raise CanonicalProblemError("invalid continuity event")
            events.append(
                ContinuityEvent(
                    problem_id=str(item["problem_id"]),
                    revision=int(item["revision"]),
                    state_digest=str(item["state_digest"]),
                    action=str(item["action"]),
                    previous_event_hash=item.get("previous_event_hash"),
                    event_hash=str(item["event_hash"]),
                )
            )
        ledger = cls(tuple(events))
        ledger.verify()
        return ledger
