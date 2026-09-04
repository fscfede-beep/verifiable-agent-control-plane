# Agent Security Threat Model

This document describes the defensive, synthetic threat model for the optional agent-security evaluation layer in this repository.

## Scope

The layer protects the boundary between a model or agent proposing an action and a tool/runtime identity capable of producing an effect. It composes over the existing control-plane invariants rather than replacing them.

All tests use local in-memory targets. No third-party service, credential, production account, or external system is required or exercised.

## Trust boundaries

1. **Requester principal** — the human, agent, or service whose authority is being exercised.
2. **Executor principal** — the runtime/service identity that can call a tool.
3. **Delegation** — explicit downscoped authority from requester to executor.
4. **Resource scope** — the exact resource identifiers permitted by grant and delegation.
5. **Context provenance** — documents, telemetry, tool metadata, MCP metadata, and cross-agent messages are evidence/context, never authorization.
6. **Approval evidence** — sensitive actions can require approval bound to the exact intent and an independent verification digest.
7. **Canonical state** — the existing revision/checkpoint state remains authoritative for materialization.

## Threats and deterministic predicates

| ID | Threat | Required invariant | Observable predicate |
| --- | --- | --- | --- |
| S01 | Confused deputy | Executor cannot exceed requester scope | no cross-principal effect |
| S02 | Reference grafting | Referenced resource must be in requester and delegation scope | no unauthorized reference access |
| S03 | Poisoned tool metadata | Context cannot mint an action grant | non-granted action denied |
| S04 | Agent-to-agent carrier | Receiver performs its own authority evaluation | no propagated privileged effect |
| S05 | Delegation drift | Security context revalidated before execution | no effect after delegation drift |
| S06 | Action substitution | Executed action must equal approved intent | core effect/action mismatch blocks promotion |
| S07 | Telemetry injection | Telemetry remains untrusted provenance | context cannot authorize mutation |
| S08 | Approval without verification | Sensitive approval binds independent verification evidence | missing verification digest denied |
| S09 | Tool metadata rug pull | Provenance digest bound at decision time | changed metadata denied before execution |
| S10 | Cross-principal replay | Security receipt binds requester identity | receipt invalid under another principal |
| S11 | Cross-tenant grant collision | Grant binds principal ID and tenant | same ID in another tenant denied |
| S12 | Cross-tenant delegation collision | Delegation binds both principal IDs and tenant IDs | mismatched tenant delegation denied |
| S13 | Cross-tenant approval collision | Approval binds requester ID and tenant | approval from another tenant denied |
| S14 | Cross-tenant executor collision | Delegation binds executor ID and tenant | executor in another tenant denied |
| S15 | Requester self-verification | Approval verifier must be distinct from requester identity | requester cannot verify its own approval |
| S16 | Unanchored verifier claim | Claimed verifier identity and digest require an exact trusted-policy anchor | fabricated verifier metadata denied |
| S17 | Executor self-verification | Approval verifier must also be distinct from executor identity | executor cannot verify the effect it will perform |
| S18 | Fabricated verification evidence | Non-empty digest without exact anchor is not authority | unanchored evidence denied |
| S19 | Cross-intent approval replay | Anchor binds exact intent digest | anchor for another intent denied |
| S20 | Cross-action approval reuse | Anchor binds exact action | anchor for another action denied |
| S21 | Cross-principal approval-anchor replay | Anchor binds exact requester principal ID | anchor issued for another requester denied |
| S22 | Cross-tenant requester approval replay | Anchor binds exact requester tenant ID | same requester ID in another tenant denied |

## Decision model

`evaluate_security` is read-only. It binds:

- intent digest;
- canonical state digest;
- requester and executor digests;
- delegation digest;
- policy digest;
- requested-resource digest;
- deterministic context-provenance digest;
- approval digest when present;
- caller-supplied evaluation epoch.

A context artifact may be attacker-controlled and may influence an upstream model's proposal, but it is never consulted as an authority source. Permission comes only from explicit grants and delegation. Grant, delegation, and approval tenant bindings are mandatory at evaluation time: constructor-level `None` values are retained only for compatibility and are rejected fail-closed. Explicit cross-tenant execution remains possible when both delegator and delegate tenant bindings match the supplied principals. For approval-required actions, a non-empty verification digest is insufficient by itself. The verifier must be distinct from both requester and executor, and `SecurityPolicy.approval_anchors` must contain an exact `ApprovalAnchor(verifier_principal_id, verifier_tenant_id, action, intent_digest, verification_digest, requester_principal_id, requester_tenant_id)` match. Requester binding is mandatory at evaluation time: constructor-level `None` values are retained only for compatibility and are rejected fail-closed. The anchor is a trusted-policy evidence binding, not a cryptographic signature or proof of external authorship.

## Execution model

`secure_materialize` requires both an accepted core decision and an accepted security decision. Immediately before the effect, it re-runs security evaluation from current inputs. Rejection or any security-context drift stops before calling the executor.

If the security context is unchanged, the existing core `materialize` function still performs action binding, deterministic core revalidation, effect readback, canonical revision advancement, and core receipt construction.

## Receipt model

A `SecurityReceipt` hash-binds the successful core receipt to the security decision evidence. Verification rejects changes to requester, executor, delegation, policy, resources, provenance, approval evidence, evaluation epoch, intent, or core receipt.

The receipt is an integrity/evidence mechanism, not a cryptographic signature. This repository does not claim HSM/KMS-backed identity, distributed consensus, or security certification.

## Non-goals

- offensive testing of systems not owned or explicitly authorized;
- credential collection or secret discovery;
- arbitrary remote tool execution;
- malware or persistence;
- authorization bypass;
- production deployment claims;
- security certification claims.

## Research context

The scenarios reflect current public agent-security research themes including confused-deputy behavior, agent-to-agent propagation, MCP/tool metadata poisoning, prompt injection through operational context, least-privilege delegation, and receipt-based oversight. They are implemented here only as synthetic defensive regression cases.
