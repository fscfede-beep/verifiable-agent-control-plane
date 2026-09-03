from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from typing import Any, Callable, Mapping


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _contains_secret_like_key(value: Any) -> bool:
    secret_markers = {
        "api_key",
        "apikey",
        "password",
        "passwd",
        "secret",
        "token",
        "authorization",
        "private_key",
    }
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in secret_markers:
                return True
            if _contains_secret_like_key(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_secret_like_key(item) for item in value)
    return False


@dataclass(frozen=True)
class CanonicalState:
    revision: int = 0
    checkpoint: str = "ZERO"
    processed_intents: tuple[str, ...] = ()
    previous_receipt_hash: str | None = None

    @property
    def digest(self) -> str:
        return _hash(
            {
                "revision": self.revision,
                "checkpoint": self.checkpoint,
                "processed_intents": list(self.processed_intents),
                "previous_receipt_hash": self.previous_receipt_hash,
            }
        )


@dataclass(frozen=True)
class Intent:
    intent_id: str
    expected_revision: int
    expected_checkpoint: str
    action: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def digest(self) -> str:
        return _hash(
            {
                "intent_id": self.intent_id,
                "expected_revision": self.expected_revision,
                "expected_checkpoint": self.expected_checkpoint,
                "action": self.action,
                "payload": dict(self.payload),
            }
        )


@dataclass(frozen=True)
class Policy:
    allowed_actions: frozenset[str]

    def allows(self, action: str) -> bool:
        return action in self.allowed_actions


@dataclass(frozen=True)
class Decision:
    intent_id: str
    intent_digest: str
    state_digest: str
    accepted: bool
    reason: str


@dataclass(frozen=True)
class EffectResult:
    effect_id: str
    action: str
    requested_payload: Mapping[str, Any]
    observed_payload: Mapping[str, Any]

    @property
    def digest(self) -> str:
        return _hash(
            {
                "effect_id": self.effect_id,
                "action": self.action,
                "requested_payload": dict(self.requested_payload),
                "observed_payload": dict(self.observed_payload),
            }
        )


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    intent_id: str
    intent_digest: str
    prior_state_digest: str
    next_state_digest: str
    from_revision: int
    to_revision: int
    effect_digest: str
    previous_receipt_hash: str | None
    receipt_hash: str

    @classmethod
    def build(
        cls,
        *,
        intent: Intent,
        prior_state: CanonicalState,
        next_state_without_hash: CanonicalState,
        effect: EffectResult,
    ) -> "Receipt":
        base = {
            "intent_id": intent.intent_id,
            "intent_digest": intent.digest,
            "prior_state_digest": prior_state.digest,
            "next_state_digest": next_state_without_hash.digest,
            "from_revision": prior_state.revision,
            "to_revision": next_state_without_hash.revision,
            "effect_digest": effect.digest,
            "previous_receipt_hash": prior_state.previous_receipt_hash,
        }
        receipt_hash = _hash(base)
        return cls(
            receipt_id=f"receipt-{receipt_hash[:16]}",
            receipt_hash=receipt_hash,
            **base,
        )

    def verify(self) -> bool:
        base = {
            "intent_id": self.intent_id,
            "intent_digest": self.intent_digest,
            "prior_state_digest": self.prior_state_digest,
            "next_state_digest": self.next_state_digest,
            "from_revision": self.from_revision,
            "to_revision": self.to_revision,
            "effect_digest": self.effect_digest,
            "previous_receipt_hash": self.previous_receipt_hash,
        }
        return self.receipt_hash == _hash(base)


class ControlPlaneError(RuntimeError):
    pass


def validate_intent(intent: Intent, state: CanonicalState, policy: Policy) -> None:
    if intent.expected_revision != state.revision:
        raise ControlPlaneError("stale revision")
    if intent.expected_checkpoint != state.checkpoint:
        raise ControlPlaneError("stale checkpoint")
    if intent.intent_id in state.processed_intents:
        raise ControlPlaneError("duplicate intent")
    if not policy.allows(intent.action):
        raise ControlPlaneError("action not allowlisted")
    if _contains_secret_like_key(intent.payload):
        raise ControlPlaneError("secret-like payload rejected")


def decide(intent: Intent, state: CanonicalState, policy: Policy) -> Decision:
    try:
        validate_intent(intent, state, policy)
    except ControlPlaneError as exc:
        return Decision(
            intent_id=intent.intent_id,
            intent_digest=intent.digest,
            state_digest=state.digest,
            accepted=False,
            reason=str(exc),
        )
    return Decision(
        intent_id=intent.intent_id,
        intent_digest=intent.digest,
        state_digest=state.digest,
        accepted=True,
        reason="accepted",
    )


def materialize(
    *,
    intent: Intent,
    decision: Decision,
    state: CanonicalState,
    policy: Policy,
    execute: Callable[[str, Mapping[str, Any]], EffectResult],
) -> tuple[CanonicalState, Receipt, EffectResult]:
    if not decision.accepted:
        raise ControlPlaneError("rejected decision cannot materialize")
    if decision.intent_id != intent.intent_id or decision.intent_digest != intent.digest:
        raise ControlPlaneError("decision/intention binding mismatch")
    if decision.state_digest != state.digest:
        raise ControlPlaneError("state drift after decision")

    validate_intent(intent, state, policy)

    effect = execute(intent.action, intent.payload)
    if effect.action != intent.action:
        raise ControlPlaneError("effect action mismatch")
    if dict(effect.requested_payload) != dict(intent.payload):
        raise ControlPlaneError("effect request mismatch")
    if dict(effect.observed_payload) != dict(intent.payload):
        raise ControlPlaneError("readback mismatch")

    next_without_receipt_hash = CanonicalState(
        revision=state.revision + 1,
        checkpoint=f"R{state.revision + 1}",
        processed_intents=state.processed_intents + (intent.intent_id,),
        previous_receipt_hash=state.previous_receipt_hash,
    )
    receipt = Receipt.build(
        intent=intent,
        prior_state=state,
        next_state_without_hash=next_without_receipt_hash,
        effect=effect,
    )
    next_state = replace(
        next_without_receipt_hash,
        previous_receipt_hash=receipt.receipt_hash,
    )
    return next_state, receipt, effect


def verify_transition(
    *,
    prior_state: CanonicalState,
    next_state: CanonicalState,
    intent: Intent,
    receipt: Receipt,
    effect: EffectResult,
) -> None:
    if not receipt.verify():
        raise ControlPlaneError("receipt hash mismatch")
    if receipt.intent_id != intent.intent_id or receipt.intent_digest != intent.digest:
        raise ControlPlaneError("receipt intent mismatch")
    if receipt.prior_state_digest != prior_state.digest:
        raise ControlPlaneError("receipt prior-state mismatch")
    if receipt.from_revision != prior_state.revision:
        raise ControlPlaneError("receipt from-revision mismatch")
    if receipt.to_revision != prior_state.revision + 1:
        raise ControlPlaneError("revision must advance exactly once")
    if next_state.revision != prior_state.revision + 1:
        raise ControlPlaneError("next state revision mismatch")
    if intent.intent_id not in next_state.processed_intents:
        raise ControlPlaneError("intent missing from next state")
    if next_state.previous_receipt_hash != receipt.receipt_hash:
        raise ControlPlaneError("receipt chain mismatch")
    if receipt.effect_digest != effect.digest:
        raise ControlPlaneError("effect digest mismatch")

    expected_next_without_hash = replace(
        next_state,
        previous_receipt_hash=prior_state.previous_receipt_hash,
    )
    if receipt.next_state_digest != expected_next_without_hash.digest:
        raise ControlPlaneError("receipt next-state mismatch")


class InMemoryTarget:
    """Tiny deterministic target used by the reference implementation and tests."""

    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    def execute(self, action: str, payload: Mapping[str, Any]) -> EffectResult:
        if action != "set_value":
            raise ControlPlaneError("unsupported target action")
        key = str(payload["key"])
        value = payload["value"]
        self.values[key] = value
        observed = {"key": key, "value": self.values[key]}
        return EffectResult(
            effect_id=f"effect-{_hash({'action': action, 'payload': observed})[:16]}",
            action=action,
            requested_payload=dict(payload),
            observed_payload=observed,
        )
