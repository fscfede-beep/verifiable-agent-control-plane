# RUMBO Agent Security Lab V0.1 — Design

Date: 2026-09-04

**Target base:** `fscfede-beep/verifiable-agent-control-plane`

**Verified base SHA:** `46c368eec637a75cd2ab4e4b6b10006186697185`

**Goal:** extend the existing reference control plane with deterministic, fail-closed agent-security checks for principal identity, delegation, resource scope, untrusted-context provenance, sensitive-action approval, security-bound receipts, and cross-principal replay resistance.

## Constraints

- This remains a workstream of the existing control plane; no new Portfolio root.
- Preserve the existing `Intent -> Decision -> Materialization -> Readback -> Receipt -> Verification` pipeline.
- Do not weaken any legacy invariant.
- Runtime dependencies remain zero.
- No external network calls or credential reads in production code.
- All security scenarios use synthetic/in-memory targets only.
- `core.py` remains unchanged in the first slice unless a failing test proves an interface change is required.
- Production and security-certification claims remain `NO_GO`.

## Architecture

Add `src/verifiable_agent_control_plane/security.py` with immutable security value objects and pure evaluation functions:

- `Principal(principal_id, principal_type, tenant_id)`
- `Delegation(delegation_id, delegator_principal_id, delegate_principal_id, allowed_actions, resource_scope, active, expires_at_epoch)`
- `ContextArtifact(artifact_id, source_type, source_id, trust_class, content_digest)`
- `ActionGrant(principal_id, action, resource_scope)`
- `ApprovalEvidence(approval_id, intent_digest, principal_id, action, approved, verification_digest)`
- `SecurityPolicy(grants, approval_required_actions)`
- `SecurityDecision(...)`
- `SecurityReceipt(...)`

Public functions:

- `evaluate_security(...) -> SecurityDecision`
- `secure_materialize(...) -> tuple[CanonicalState, Receipt, SecurityReceipt, EffectResult]`
- `verify_security_transition(...) -> None`

The security evaluator is read-only. It binds requester identity, executor identity, delegation, requested resources, context provenance, policy, approval evidence, evaluation epoch, and canonical state. Materialization re-evaluates the complete security context and fails closed on drift before calling the existing core `materialize`.

## Security rules

1. The requester must have an `ActionGrant` for the action and every requested resource.
2. Delegation must bind the exact requester and executor.
3. Delegation must be active, unexpired for the supplied deterministic evaluation epoch, allow the action, and contain every requested resource.
4. Context artifacts are evidence/provenance, never authority. Untrusted tool descriptions, telemetry, retrieved documents, or cross-agent messages cannot mint permission.
5. Actions listed in `approval_required_actions` require approval bound to the exact intent, requester, action, and a non-empty independent `verification_digest`.
6. Security decision data is re-derived immediately before execution. Any changed principal, delegation, resource set, policy, approval, or provenance fails closed.
7. A `SecurityReceipt` binds the existing core receipt hash to requester, executor, delegation, resources, provenance, policy, approval evidence, and evaluation epoch.
8. Verification rejects a valid transition replayed under another principal or changed security context.

## Synthetic scenarios

- S01 confused deputy: service identity has broad technical access but requester lacks the target resource.
- S02 reference grafting: a principal supplies another principal's reference/resource ID.
- S03 poisoned tool description: attacker-controlled metadata requests a privileged action.
- S04 agent-to-agent carrier: shared-channel instructions reach a second agent without its own authority.
- S05 delegation drift: delegation becomes inactive or changes after decision.
- S06 action substitution: executor reports a different action from the approved intent.
- S07 telemetry injection: log content attempts to authorize state mutation.
- S08 approval without verification: sensitive action has no independently bound verification evidence.
- S09 tool metadata rug pull: provenance digest changes after decision.
- S10 cross-principal replay: security evidence generated for principal A is verified under principal B.

## Promotion gates

A candidate can be called `V0.1 SECURITY CANDIDATE` only when legacy tests plus all security tests pass locally, installed-package import checks pass, and the GitHub Python 3.11/3.12/3.13 matrix succeeds on the exact candidate SHA. Documentation claims must not be promoted before exact-SHA CI evidence exists.
