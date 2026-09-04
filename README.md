# Verifiable Agent Control Plane

[![test](https://github.com/fscfede-beep/verifiable-agent-control-plane/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/fscfede-beep/verifiable-agent-control-plane/actions/workflows/test.yml)

A small, runtime-dependency-free Python reference implementation for **fail-closed agent execution with explicit authority, deterministic revalidation, effect readback, and hash-bound receipts**.

This repository is a new, sanitized reference extraction of reliability patterns I use in larger agent systems. It is **not** a dump of a private production control plane, and it does not contain credentials, private state, provider IDs, or proprietary deployment configuration.

## Public verification

The public `test` workflow installs the project from source, runs the unit suite on Python **3.11, 3.12, and 3.13**, and verifies the installed import surface outside the repository checkout.

Stable release evidence and the exact local/public claim boundary are recorded in [`CLAIMS.md`](CLAIMS.md). Packaging changes are not promoted or released until the public matrix passes on the exact candidate SHA.

## Why this exists

Agent systems often blur several different facts:

1. the model proposed an action;
2. the action was authorized;
3. the action was executed;
4. the intended effect actually happened;
5. the resulting state is safe to promote.

Those are not the same event.

This reference keeps them separate:

```text
INTENT
  ↓ exact revision/checkpoint binding
AUTHORITY / DECISION (read-only)
  ↓ deterministic revalidation
MATERIALIZATION
  ↓ allowlisted effect
READBACK
  ↓
RECEIPT
  ↓
VERIFICATION / PROMOTION
```

## Core invariants

- **Read-only decision phase.** A decision does not mutate canonical state.
- **Exact-state binding.** Intents bind to an expected revision and checkpoint.
- **Stale decisions fail closed.** State drift between decision and execution blocks materialization.
- **Action allowlist.** Only explicitly permitted actions may execute.
- **Secret-like payload rejection.** Obvious credential-bearing keys are rejected before execution.
- **One revision per accepted intent.** A materialization advances state exactly once.
- **Readback before success.** Requested payload and observed effect must match.
- **Immutable intent identity.** The same intent cannot be processed twice.
- **Hash-bound receipt chain.** Each receipt binds intent, prior state, next state, effect, and previous receipt hash.
- **Verification before promotion.** Tampered receipts or inconsistent transitions are rejected.

## Install from source

Requires Python 3.11+.

```bash
python -m pip install .
```

Then import the public package as:

```python
import verifiable_agent_control_plane
```

The legacy top-level import `verifiable_control_plane` remains as a compatibility shim. This project is installable from source but is **not published to PyPI**.

## Latest release

[`v0.2.0`](https://github.com/fscfede-beep/verifiable-agent-control-plane/releases/tag/v0.2.0) provides the installable reference package plus a wheel asset and `SHA256SUMS.txt` for the exact uploaded file. Bit-for-bit wheel rebuild reproducibility is not claimed.

## Run the tests

```bash
python -m pip install .
python -m unittest discover -s tests -v
```

The suite covers:

- exact-state acceptance;
- stale revision/checkpoint rejection;
- duplicate-intent rejection;
- action allowlisting;
- secret-like payload rejection;
- read-only decision behavior;
- one-revision materialization;
- state-drift rejection;
- rejected-decision enforcement;
- effect readback mismatch;
- receipt-chain verification;
- receipt tamper detection;
- replay prevention.

## Minimal example

```python
from verifiable_agent_control_plane import (
    CanonicalState, Intent, Policy, InMemoryTarget,
    decide, materialize, verify_transition,
)

state = CanonicalState()
intent = Intent(
    intent_id="intent-001",
    expected_revision=0,
    expected_checkpoint="ZERO",
    action="set_value",
    payload={"key": "mode", "value": "safe"},
)
policy = Policy(frozenset({"set_value"}))

decision = decide(intent, state, policy)
target = InMemoryTarget()

next_state, receipt, effect = materialize(
    intent=intent,
    decision=decision,
    state=state,
    policy=policy,
    execute=target.execute,
)

verify_transition(
    prior_state=state,
    next_state=next_state,
    intent=intent,
    receipt=receipt,
    effect=effect,
)
```

## Agent security evaluation

The agent-security layer composes over the core control plane with explicit requester/executor identity, downscoped delegation, resource grants, deterministic context provenance, approval evidence for sensitive actions, pre-execution security revalidation, and security receipts bound to the core receipt.

It is designed to make common agent/tool boundary failures reproducible with synthetic tests, including confused-deputy access, cross-principal reference grafting, untrusted MCP/tool metadata, agent-to-agent instruction carriers, delegation drift, action substitution, telemetry injection, weak approval evidence, metadata rug pulls, cross-principal replay, and cross-tenant identity collisions.

Authority artifacts are tenant-bound. Grants bind the requester tenant, delegations bind both delegator and delegate tenants, and approvals bind the approving requester tenant. Omitted tenant bindings are rejected fail-closed during evaluation; explicit cross-tenant delegation remains supported when both sides are bound to the supplied principals.

See [`docs/AGENT_SECURITY_THREAT_MODEL.md`](docs/AGENT_SECURITY_THREAT_MODEL.md) for the threat model and explicit non-goals.

This layer does **not** turn the project into a production security product and does not claim certification, third-party penetration testing, or complete protection against all agentic attacks.
## What this does *not* claim

- No production deployment claim.
- No security certification.
- No cryptographic signature / HSM / KMS integration.
- No distributed consensus.
- No external model or provider call.
- No OpenAI endorsement, merge, employment, or affiliation.
- No claim that this repository is the original private system from which the pattern was extracted.

The point is narrower: make authority and effect verification **observable, testable, and difficult to accidentally conflate**.

## Related public engineering work

- OpenAI Codex issue #42367 — independent revalidation + public reference implementation:
  https://github.com/openai/codex/issues/42367
- OpenAI Agents SDK issues #4747 and #4749 — async resource ownership / cancellation boundaries:
  https://github.com/openai/openai-agents-python/issues/4747
  https://github.com/openai/openai-agents-python/issues/4749
- Technical portfolio:
  https://sebastian-ai-workflow-reliability.miniup.app

## Author

Sebastián — AI Systems & Agent Reliability Engineer · Founder, RUMBO IA

RUMBO public surfaces: [rumbo.verso.fans](https://rumbo.verso.fans/) · [@RumboAGI on X](https://x.com/RumboAGI)
