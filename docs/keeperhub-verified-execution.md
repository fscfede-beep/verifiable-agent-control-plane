# RUMBO Verified Execution × KeeperHub

## Goal

Demonstrate a narrow integration boundary between probabilistic agent intent and
deterministic external execution.

The control plane decides whether an action is allowed. KeeperHub executes only
the exact workflow that passed that gate. RUMBO then hashes the request and
response into an evidence receipt and requires readback before declaring success.

## Safety posture

The demo is fail-closed:

- `GET /api/chains` is the default connectivity probe and needs no API key.
- Private workflow listing requires `KEEPERHUB_API_KEY`.
- Workflow execution requires both an API key and explicit `--allow-execution`.
- One client instance can start at most one workflow execution.
- A final claim of success requires KeeperHub's `/wait` result to report
  `completed: true` and `status: success`.
- The adapter exposes no direct on-chain broadcast method.
- The direct-transfer helper always emits `simulate: true`.
- Secrets are read from environment variables and are never included in receipts.

## Quick start

Run the repository tests first:

```bash
python -m unittest discover -s tests -v
```

Public connectivity probe:

```bash
python examples/keeperhub_verified_execution.py
```

Authenticated workflow discovery:

```bash
set KEEPERHUB_API_KEY=kh_your_key_here
python examples/keeperhub_verified_execution.py --list-workflows
```

Exactly one explicitly authorized workflow execution:

```bash
python examples/keeperhub_verified_execution.py \
  --execute-workflow YOUR_WORKFLOW_ID \
  --allow-execution \
  --wait
```

## Evidence model

Every API operation produces a `KeeperHubReceipt` containing:

- operation name;
- endpoint;
- SHA-256 of the canonical request body;
- SHA-256 of the canonical response body;
- KeeperHub request ID when supplied;
- execution ID when supplied;
- observed status.

The receipt proves what this client requested and what it observed. It does not
claim that an on-chain effect occurred unless KeeperHub's terminal readback says
success and the corresponding transaction receipts are present.

## Direct-value movement remains gated

KeeperHub documents a safe direct-execution sequence: select an enabled testnet,
simulate the exact request, proceed only when simulation succeeds and would not
revert, use a stable `Idempotency-Key` for the single broadcast, then read the
execution status and verified receipts back from the chain.

This demo intentionally implements only the simulation payload builder. A future
broadcast path should be added only after explicit value, recipient, testnet,
idempotency, and spending-limit policy gates exist.

## Submission narrative

**Problem:** AI agents are probabilistic, while payments and contract calls are
irreversible state transitions.

**Approach:** RUMBO turns a proposed action into a policy decision and evidence
record. KeeperHub is the deterministic execution boundary. The result is read
back and reconciled into a receipt before the action is treated as complete.

**Why KeeperHub is essential:** the project does not reimplement wallet custody,
workflow execution, gas handling, or transaction settlement. It constrains and
verifies how an agent is allowed to invoke those capabilities.

## Authoritative KeeperHub references

- API overview: https://docs.keeperhub.com/api
- Getting started with workflow execution: https://docs.keeperhub.com/getting-started/api
- Workflow API: https://docs.keeperhub.com/api/workflows
- Execution receipts/status: https://docs.keeperhub.com/api/executions
- Direct execution and simulation: https://docs.keeperhub.com/api/direct-execution
