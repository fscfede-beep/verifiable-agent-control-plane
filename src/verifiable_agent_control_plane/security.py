from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from .core import (
    CanonicalState,
    ControlPlaneError,
    Decision,
    EffectResult,
    Intent,
    Policy,
    Receipt,
    materialize,
    verify_transition,
)


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
class ContextArtifact:
    artifact_id: str
    source_type: str
    source_id: str
    trust_class: str
    content_digest: str

    @property
    def digest(self) -> str:
        return _hash(
            {
                "artifact_id": self.artifact_id,
                "source_type": self.source_type,
                "source_id": self.source_id,
                "trust_class": self.trust_class,
                "content_digest": self.content_digest,
            }
        )


def _provenance_digest(artifacts: tuple[ContextArtifact, ...]) -> str:
    normalized = sorted(
        (
            {
                "artifact_id": artifact.artifact_id,
                "artifact_digest": artifact.digest,
            }
            for artifact in artifacts
        ),
        key=lambda item: (item["artifact_id"], item["artifact_digest"]),
    )
    return _hash(normalized)


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
class ApprovalEvidence:
    approval_id: str
    intent_digest: str
    principal_id: str
    action: str
    approved: bool
    verification_digest: str | None

    @property
    def digest(self) -> str:
        return _hash(
            {
                "approval_id": self.approval_id,
                "intent_digest": self.intent_digest,
                "principal_id": self.principal_id,
                "action": self.action,
                "approved": self.approved,
                "verification_digest": self.verification_digest,
            }
        )


@dataclass(frozen=True)
class SecurityPolicy:
    grants: tuple[ActionGrant, ...]
    approval_required_actions: frozenset[str] = frozenset()

    @property
    def digest(self) -> str:
        normalized_grants = sorted(
            (grant.payload() for grant in self.grants),
            key=lambda item: (
                item["principal_id"],
                item["action"],
                tuple(item["resource_scope"]),
            ),
        )
        return _hash(
            {
                "grants": normalized_grants,
                "approval_required_actions": sorted(self.approval_required_actions),
            }
        )


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
    provenance_digest: str
    approval_digest: str | None
    evaluation_epoch: int
    accepted: bool
    reason: str


@dataclass(frozen=True)
class SecurityReceipt:
    receipt_id: str
    core_receipt_hash: str
    intent_digest: str
    requester_digest: str
    executor_digest: str
    delegation_digest: str
    policy_digest: str
    requested_resources_digest: str
    provenance_digest: str
    approval_digest: str | None
    evaluation_epoch: int
    security_receipt_hash: str

    @classmethod
    def build(
        cls,
        *,
        core_receipt: Receipt,
        security_decision: SecurityDecision,
    ) -> "SecurityReceipt":
        base = {
            "core_receipt_hash": core_receipt.receipt_hash,
            "intent_digest": security_decision.intent_digest,
            "requester_digest": security_decision.requester_digest,
            "executor_digest": security_decision.executor_digest,
            "delegation_digest": security_decision.delegation_digest,
            "policy_digest": security_decision.policy_digest,
            "requested_resources_digest": security_decision.requested_resources_digest,
            "provenance_digest": security_decision.provenance_digest,
            "approval_digest": security_decision.approval_digest,
            "evaluation_epoch": security_decision.evaluation_epoch,
        }
        security_receipt_hash = _hash(base)
        return cls(
            receipt_id=f"security-receipt-{security_receipt_hash[:16]}",
            security_receipt_hash=security_receipt_hash,
            **base,
        )

    def verify(self) -> bool:
        base = {
            "core_receipt_hash": self.core_receipt_hash,
            "intent_digest": self.intent_digest,
            "requester_digest": self.requester_digest,
            "executor_digest": self.executor_digest,
            "delegation_digest": self.delegation_digest,
            "policy_digest": self.policy_digest,
            "requested_resources_digest": self.requested_resources_digest,
            "provenance_digest": self.provenance_digest,
            "approval_digest": self.approval_digest,
            "evaluation_epoch": self.evaluation_epoch,
        }
        return self.security_receipt_hash == _hash(base)


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
    artifacts: tuple[ContextArtifact, ...] = (),
    approval: ApprovalEvidence | None = None,
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
            provenance_digest=_provenance_digest(artifacts),
            approval_digest=approval.digest if approval is not None else None,
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

    if intent.action in policy.approval_required_actions:
        if approval is None:
            return result(False, "approval required")
        if approval.intent_digest != intent.digest:
            return result(False, "approval intent mismatch")
        if approval.principal_id != requester.principal_id:
            return result(False, "approval principal mismatch")
        if approval.action != intent.action:
            return result(False, "approval action mismatch")
        if not approval.approved:
            return result(False, "approval not granted")
        if not approval.verification_digest:
            return result(False, "independent verification required")

    return result(True, "accepted")


def secure_materialize(
    *,
    intent: Intent,
    core_decision: Decision,
    security_decision: SecurityDecision,
    state: CanonicalState,
    core_policy: Policy,
    requester: Principal,
    executor: Principal,
    delegation: Delegation,
    security_policy: SecurityPolicy,
    requested_resources: frozenset[str],
    evaluation_epoch: int,
    execute: Callable[[str, Mapping[str, Any]], EffectResult],
    artifacts: tuple[ContextArtifact, ...] = (),
    approval: ApprovalEvidence | None = None,
) -> tuple[CanonicalState, Receipt, SecurityReceipt, EffectResult]:
    if not security_decision.accepted:
        raise ControlPlaneError("rejected security decision cannot materialize")

    current_security_decision = evaluate_security(
        intent=intent,
        requester=requester,
        executor=executor,
        delegation=delegation,
        policy=security_policy,
        state=state,
        requested_resources=requested_resources,
        evaluation_epoch=evaluation_epoch,
        artifacts=artifacts,
        approval=approval,
    )
    if not current_security_decision.accepted:
        raise ControlPlaneError(
            f"security context no longer accepted: {current_security_decision.reason}"
        )
    if current_security_decision != security_decision:
        raise ControlPlaneError("security context drift after decision")

    next_state, core_receipt, effect = materialize(
        intent=intent,
        decision=core_decision,
        state=state,
        policy=core_policy,
        execute=execute,
    )
    security_receipt = SecurityReceipt.build(
        core_receipt=core_receipt,
        security_decision=current_security_decision,
    )
    return next_state, core_receipt, security_receipt, effect


def verify_security_transition(
    *,
    prior_state: CanonicalState,
    next_state: CanonicalState,
    intent: Intent,
    core_receipt: Receipt,
    security_receipt: SecurityReceipt,
    effect: EffectResult,
    requester: Principal,
    executor: Principal,
    delegation: Delegation,
    security_policy: SecurityPolicy,
    requested_resources: frozenset[str],
    evaluation_epoch: int,
    artifacts: tuple[ContextArtifact, ...] = (),
    approval: ApprovalEvidence | None = None,
) -> None:
    verify_transition(
        prior_state=prior_state,
        next_state=next_state,
        intent=intent,
        receipt=core_receipt,
        effect=effect,
    )

    if not security_receipt.verify():
        raise ControlPlaneError("security receipt hash mismatch")
    if security_receipt.core_receipt_hash != core_receipt.receipt_hash:
        raise ControlPlaneError("security/core receipt mismatch")
    if security_receipt.intent_digest != intent.digest:
        raise ControlPlaneError("security intent mismatch")
    if security_receipt.requester_digest != requester.digest:
        raise ControlPlaneError("security requester mismatch")
    if security_receipt.executor_digest != executor.digest:
        raise ControlPlaneError("security executor mismatch")
    if security_receipt.delegation_digest != delegation.digest:
        raise ControlPlaneError("security delegation mismatch")
    if security_receipt.policy_digest != security_policy.digest:
        raise ControlPlaneError("security policy mismatch")
    if security_receipt.requested_resources_digest != _resource_digest(requested_resources):
        raise ControlPlaneError("security resource scope mismatch")
    if security_receipt.provenance_digest != _provenance_digest(artifacts):
        raise ControlPlaneError("security provenance mismatch")
    approval_digest = approval.digest if approval is not None else None
    if security_receipt.approval_digest != approval_digest:
        raise ControlPlaneError("security approval mismatch")
    if security_receipt.evaluation_epoch != evaluation_epoch:
        raise ControlPlaneError("security evaluation epoch mismatch")
