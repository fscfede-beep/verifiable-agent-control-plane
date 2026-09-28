from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from typing import Any, Mapping


SCHEMA = "rumbo-grok-transport-envelope-v1"
_ALLOWED_KINDS = frozenset({"evidence_handoff", "ack", "capability_probe"})
_ALLOWED_TARGETS = frozenset({"OPENAI_CHATGPT_PRIMARY"})
_SECRET_KEYS = frozenset(
    {"api_key", "apikey", "password", "passwd", "secret", "token", "authorization", "private_key"}
)


def _stable_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TransportCandidateError("payload is not canonical-json serializable") from exc


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _contains_secret_like_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in _SECRET_KEYS:
                return True
            if _contains_secret_like_key(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_secret_like_key(item) for item in value)
    return False


def _required_text(name: str, value: str, *, max_length: int = 256) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TransportCandidateError(f"{name} is required")
    if len(value) > max_length:
        raise TransportCandidateError(f"{name} exceeds maximum length")


class TransportCandidateError(RuntimeError):
    pass


@dataclass(frozen=True)
class HumanKillSwitch:
    """Human-controlled gate. Disabled is the safe/default state."""

    enabled: bool = False


@dataclass(frozen=True)
class GrokTransportEnvelope:
    schema: str
    message_id: str
    idempotency_key: str
    nonce: str
    from_node: str
    to_node: str
    kind: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def digest(self) -> str:
        return _hash(
            {
                "schema": self.schema,
                "message_id": self.message_id,
                "idempotency_key": self.idempotency_key,
                "nonce": self.nonce,
                "from_node": self.from_node,
                "to_node": self.to_node,
                "kind": self.kind,
                "payload": dict(self.payload),
            }
        )


@dataclass(frozen=True)
class GrokTransportReceipt:
    receipt_id: str
    candidate_node_id: str
    envelope_digest: str
    message_id: str
    idempotency_key: str
    nonce: str
    sequence: int
    previous_receipt_hash: str | None
    status: str
    receipt_hash: str

    @classmethod
    def build(
        cls,
        *,
        candidate_node_id: str,
        envelope: GrokTransportEnvelope,
        sequence: int,
        previous_receipt_hash: str | None,
    ) -> "GrokTransportReceipt":
        base = {
            "candidate_node_id": candidate_node_id,
            "envelope_digest": envelope.digest,
            "message_id": envelope.message_id,
            "idempotency_key": envelope.idempotency_key,
            "nonce": envelope.nonce,
            "sequence": sequence,
            "previous_receipt_hash": previous_receipt_hash,
            "status": "ACCEPTED",
        }
        receipt_hash = _hash(base)
        return cls(
            receipt_id=f"grok-receipt-{receipt_hash[:16]}",
            receipt_hash=receipt_hash,
            **base,
        )

    def verify(self) -> bool:
        base = {
            "candidate_node_id": self.candidate_node_id,
            "envelope_digest": self.envelope_digest,
            "message_id": self.message_id,
            "idempotency_key": self.idempotency_key,
            "nonce": self.nonce,
            "sequence": self.sequence,
            "previous_receipt_hash": self.previous_receipt_hash,
            "status": self.status,
        }
        return self.receipt_hash == _hash(base)


@dataclass(frozen=True)
class GrokTransportState:
    sequence: int = 0
    seen_nonces: tuple[str, ...] = ()
    seen_message_ids: tuple[str, ...] = ()
    idempotency_keys: tuple[str, ...] = ()
    receipts: tuple[GrokTransportReceipt, ...] = ()
    previous_receipt_hash: str | None = None

    def receipt_for_idempotency_key(self, key: str) -> GrokTransportReceipt | None:
        for receipt in self.receipts:
            if receipt.idempotency_key == key:
                return receipt
        return None


@dataclass(frozen=True)
class TransportCandidate:
    """Non-authoritative, non-production transport candidate.

    This object validates and records candidate envelopes only. It performs no
    network I/O and cannot promote control-plane or production state.
    """

    node_id: str
    status: str = field(default="CANDIDATE", init=False)
    is_authority: bool = field(default=False, init=False)
    is_production: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        _required_text("node_id", self.node_id)

    def _validate_envelope(self, envelope: GrokTransportEnvelope) -> None:
        if envelope.schema != SCHEMA:
            raise TransportCandidateError("schema mismatch")
        _required_text("message_id", envelope.message_id)
        _required_text("idempotency_key", envelope.idempotency_key)
        _required_text("nonce", envelope.nonce)
        _required_text("from_node", envelope.from_node)
        _required_text("to_node", envelope.to_node)
        _required_text("kind", envelope.kind)
        if envelope.from_node != self.node_id:
            raise TransportCandidateError("source node mismatch")
        if envelope.to_node not in _ALLOWED_TARGETS:
            raise TransportCandidateError("target node not allowlisted")
        if envelope.kind not in _ALLOWED_KINDS:
            raise TransportCandidateError("kind not allowlisted")
        if not isinstance(envelope.payload, Mapping):
            raise TransportCandidateError("payload must be a mapping")
        if _contains_secret_like_key(envelope.payload):
            raise TransportCandidateError("secret-like payload rejected")
        _stable_json(dict(envelope.payload))

    def accept(
        self,
        *,
        envelope: GrokTransportEnvelope,
        state: GrokTransportState,
        kill_switch: HumanKillSwitch,
    ) -> tuple[GrokTransportState, GrokTransportReceipt]:
        if not isinstance(kill_switch, HumanKillSwitch) or not kill_switch.enabled:
            raise TransportCandidateError("human kill switch is not enabled")

        self._validate_envelope(envelope)

        prior_receipt = state.receipt_for_idempotency_key(envelope.idempotency_key)
        if prior_receipt is not None:
            if prior_receipt.envelope_digest != envelope.digest:
                raise TransportCandidateError("idempotency conflict")
            return state, prior_receipt

        if envelope.nonce in state.seen_nonces:
            raise TransportCandidateError("replay nonce")
        if envelope.message_id in state.seen_message_ids:
            raise TransportCandidateError("duplicate message id")

        receipt = GrokTransportReceipt.build(
            candidate_node_id=self.node_id,
            envelope=envelope,
            sequence=state.sequence + 1,
            previous_receipt_hash=state.previous_receipt_hash,
        )
        next_state = replace(
            state,
            sequence=state.sequence + 1,
            seen_nonces=state.seen_nonces + (envelope.nonce,),
            seen_message_ids=state.seen_message_ids + (envelope.message_id,),
            idempotency_keys=state.idempotency_keys + (envelope.idempotency_key,),
            receipts=state.receipts + (receipt,),
            previous_receipt_hash=receipt.receipt_hash,
        )
        return next_state, receipt
