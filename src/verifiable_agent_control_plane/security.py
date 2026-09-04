from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .core import CanonicalState, Intent


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _resource_digest(resources: frozenset[str]) -> str:
    return _hash(sorted(resources))


@dataclass(frozen=True)
class Principal:
    principal_id: str
    principal_type: str
    tenant_id: str

    @property
    def digest(self) -> str:
        return _hash(
            {
                "principal_id": self.principal_id,
                "principal_type": self.principal_type,
                "tenant_id": self.tenant_id,
            }
        )


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    delegator_principal_id: str
    delegate_principal_id: str
    allowed_actions: frozenset[str]
    resource_scope: frozenset[str]
    active: bool = True
    expires_at_epoch: int | None = None

    @property
    def digest(self) -> str:
        return _hash(
            {
                "delegation_id": self.delegation_id,
                "delegator_principal_id": self.delegator_principal_id,
                "delegate_principal_id": self.delegate_principal_id,
                "allowed_actions": sorted(self.allowed_actions),
                "resource_scope": sorted(self.resource_scope),
                "active": self.active,
                "expires_at_epoch": self.expires_at_epoch,
            }
        )


@dataclass(frozen=True)
class ActionGrant:
    principal_id: str
    action: str
    resource_scope: frozenset[str]

    def payload(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "action": self.action,
            "resource_scope": sorted(self.resource_scope),
        }


@dataclass(frozen=True)
class SecurityPolicy:
    grants: tuple[ActionGrant, ...]

    @property
    def digest(self) -> str:
        normalized = sorted(
            (grant.payload() for grant in self.grants),
            key=lambda item: (
                item["principal_id"],
                item["action"],
                tuple(item["resource_scope"]),
            ),
        )
        return _hash(normalized)


@dataclass(frozen=True)
class SecurityDecision:
    intent_id: str
    intent_digest: str
    state_digest: str
    requester_digest: str
    executor_digest: str
    delegation_digest: str
    policy_digest: str
    requested_resources_digest: str
    evaluation_epoch: int
    accepted: bool
    reason: str


def evaluate_security(
    *,
    intent: Intent,
    requester: Principal,
    executor: Principal,
    delegation: Delegation,
    policy: SecurityPolicy,
    state: CanonicalState,
    requested_resources: frozenset[str],
    evaluation_epoch: int,
) -> SecurityDecision:
    def result(accepted: bool, reason: str) -> SecurityDecision:
        return SecurityDecision(
            intent_id=intent.intent_id,
            intent_digest=intent.digest,
            state_digest=state.digest,
            requester_digest=requester.digest,
            executor_digest=executor.digest,
            delegation_digest=delegation.digest,
            policy_digest=policy.digest,
            requested_resources_digest=_resource_digest(requested_resources),
            evaluation_epoch=evaluation_epoch,
            accepted=accepted,
            reason=reason,
        )

    grants = tuple(
        grant
        for grant in policy.grants
        if grant.principal_id == requester.principal_id and grant.action == intent.action
    )
    if not grants:
        return result(False, "principal not permitted for action")
    if not any(requested_resources.issubset(grant.resource_scope) for grant in grants):
        return result(False, "resource outside principal scope")

    if delegation.delegator_principal_id != requester.principal_id:
        return result(False, "delegation requester mismatch")
    if delegation.delegate_principal_id != executor.principal_id:
        return result(False, "delegation executor mismatch")
    if not delegation.active:
        return result(False, "delegation inactive")
    if (
        delegation.expires_at_epoch is not None
        and evaluation_epoch >= delegation.expires_at_epoch
    ):
        return result(False, "delegation expired")
    if intent.action not in delegation.allowed_actions:
        return result(False, "delegation action not permitted")
    if not requested_resources.issubset(delegation.resource_scope):
        return result(False, "resource outside delegation scope")

    return result(True, "accepted")
