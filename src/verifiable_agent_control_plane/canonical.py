from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping


SCHEMA_VERSION = "1.1"
BRAND = "RUMBO IA"
BRAND_NAMESPACE = "RUMBO-IA"

_STATUS_VALUES = {
    "DISCOVERY",
    "EVIDENCE",
    "RECONCILIATION",
    "SOLVING",
    "VERIFYING",
    "VERIFIED",
    "VERIFIED_PENDING_EXTERNAL_GATE",
    "FAIL_CLOSED",
}
_EVIDENCE_STATUS_VALUES = {"verified", "stale", "contradictory", "unavailable"}
_FORBIDDEN_KEY_MARKERS = {
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "private_key",
    "cookie",
}


class CanonicalProblemError(ValueError):
    """Raised when canonical problem state violates its safety contract."""


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _contains_forbidden_material(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_KEY_MARKERS:
                return True
            if _contains_forbidden_material(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_material(item) for item in value)
    return False


@dataclass(frozen=True)
class Evidence:
    source: str
    kind: str
    locator: str
    observed_at: str
    digest: str
    status: str = "verified"

    def validate(self) -> None:
        if not all(isinstance(item, str) and item for item in (
            self.source, self.kind, self.locator, self.observed_at, self.digest
        )):
            raise CanonicalProblemError("evidence fields must be non-empty strings")
        if self.status not in _EVIDENCE_STATUS_VALUES:
            raise CanonicalProblemError("invalid evidence status")
        if not self.digest.startswith("sha256:") or len(self.digest) != 71:
            raise CanonicalProblemError("evidence digest must be sha256:<64 hex chars>")


@dataclass(frozen=True)
class CanonicalProblemState:
    problem_id: str
    brand: str
    brand_record_id: str
    title: str
    objective: str
    status: str
    revision: int = 0
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    evidence: tuple[Evidence, ...] = ()
    decisions: tuple[str, ...] = ()
    artifacts: tuple[Mapping[str, str], ...] = ()
    verification: Mapping[str, Any] = field(default_factory=dict)
    next_actions: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.brand != BRAND:
            raise CanonicalProblemError("canonical state must be registered under RUMBO IA")
        if self.brand_record_id is None:
            raise CanonicalProblemError("canonical state requires RUMBO IA record id")
        if not self.brand_record_id.startswith(BRAND_NAMESPACE + "/"):
            raise CanonicalProblemError("invalid RUMBO IA record id")
        if self.status not in _STATUS_VALUES:
            raise CanonicalProblemError("invalid canonical status")
        if not all(isinstance(item, str) and item for item in (
            self.problem_id, self.title, self.objective, self.created_at, self.updated_at
        )):
            raise CanonicalProblemError("canonical identity fields must be non-empty strings")
        if self.revision < 0:
            raise CanonicalProblemError("revision must be non-negative")
        for item in self.evidence:
            item.validate()
        if any(not isinstance(decision, str) or not decision for decision in self.decisions):
            raise CanonicalProblemError("decisions must contain non-empty strings")
        for artifact in self.artifacts:
            if not isinstance(artifact, Mapping):
                raise CanonicalProblemError("artifacts must be mappings")
            if not all(
                isinstance(k, str) and isinstance(v, str) and v
                for k, v in artifact.items()
            ):
                raise CanonicalProblemError("artifact fields must be string pairs")
        if _contains_forbidden_material(self.to_dict()):
            raise CanonicalProblemError("canonical state contains secret-like material")
        if self.status == "VERIFIED" and any(
            evidence.status != "verified" for evidence in self.evidence
        ):
            raise CanonicalProblemError(
                "VERIFIED state requires every evidence item to be verified"
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CanonicalProblemState":
        """Reconstruct canonical state from a durable, sanitized record."""
        if data.get("schema_version") != SCHEMA_VERSION:
            raise CanonicalProblemError("unsupported canonical schema version")
        raw_evidence = data.get("evidence", [])
        if not isinstance(raw_evidence, list):
            raise CanonicalProblemError("evidence must be a list")
        evidence = tuple(
            Evidence(
                source=item["source"],
                kind=item["kind"],
                locator=item["locator"],
                observed_at=item["observed_at"],
                digest=item["digest"],
                status=item.get("status", "verified"),
            )
            for item in raw_evidence
        )
        state = cls(
            problem_id=str(data["problem_id"]),
            brand=str(data.get("brand", "")),
            brand_record_id=data.get("brand_record_id"),
            title=str(data["title"]),
            objective=str(data["objective"]),
            status=str(data["status"]),
            revision=int(data["revision"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            evidence=evidence,
            decisions=tuple(data.get("decisions", [])),
            artifacts=tuple(data.get("artifacts", [])),
            verification=dict(data.get("verification", {})),
            next_actions=tuple(data.get("next_actions", [])),
        )
        state.validate()
        return state

    @classmethod
    def from_json(cls, payload: str) -> "CanonicalProblemState":
        """Reconstruct state from serialized JSON."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CanonicalProblemError("invalid canonical JSON") from exc
        if not isinstance(data, Mapping):
            raise CanonicalProblemError("canonical JSON root must be an object")
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Serialize canonical state deterministically for cross-chat transfer."""
        return _stable_json(self.to_dict())

    @property
    def digest(self) -> str:
        self.validate()
        return _digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "brand": self.brand,
            "brand_record_id": self.brand_record_id,
            "problem_id": self.problem_id,
            "title": self.title,
            "objective": self.objective,
            "status": self.status,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "evidence": [
                {
                    "source": item.source,
                    "kind": item.kind,
                    "locator": item.locator,
                    "observed_at": item.observed_at,
                    "digest": item.digest,
                    "status": item.status,
                }
                for item in self.evidence
            ],
            "decisions": list(self.decisions),
            "artifacts": [dict(item) for item in self.artifacts],
            "verification": dict(self.verification),
            "next_actions": list(self.next_actions),
        }


def resume_state(state: CanonicalProblemState) -> dict[str, Any]:
    """Return the minimal actionable package for a fresh chat/session."""
    state.validate()
    return {
        "problem_id": state.problem_id,
        "revision": state.revision,
        "objective": state.objective,
        "status": state.status,
        "verified_evidence": [
            item.locator for item in state.evidence if item.status == "verified"
        ],
        "unresolved_evidence": [
            item.locator for item in state.evidence if item.status != "verified"
        ],
        "decisions": list(state.decisions),
        "verification": dict(state.verification),
        "next_actions": list(state.next_actions),
        "state_digest": state.digest,
    }


def advance(
    state: CanonicalProblemState,
    *,
    status: str,
    evidence: tuple[Evidence, ...] | None = None,
    decisions: tuple[str, ...] | None = None,
    artifacts: tuple[Mapping[str, str], ...] | None = None,
    verification: Mapping[str, Any] | None = None,
    next_actions: tuple[str, ...] | None = None,
) -> CanonicalProblemState:
    """Create exactly one new canonical revision."""
    state.validate()
    if status not in _STATUS_VALUES:
        raise CanonicalProblemError("invalid canonical status")
    updated = CanonicalProblemState(
        problem_id=state.problem_id,
        brand=state.brand,
        brand_record_id=state.brand_record_id,
        title=state.title,
        objective=state.objective,
        status=status,
        revision=state.revision + 1,
        created_at=state.created_at,
        updated_at=_utcnow(),
        evidence=state.evidence if evidence is None else evidence,
        decisions=state.decisions if decisions is None else decisions,
        artifacts=state.artifacts if artifacts is None else artifacts,
        verification=state.verification if verification is None else verification,
        next_actions=state.next_actions if next_actions is None else next_actions,
    )
    updated.validate()
    return updated
