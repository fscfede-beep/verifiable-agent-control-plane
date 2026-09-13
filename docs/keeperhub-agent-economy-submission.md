# KeeperHub Agent Economy Hackathon — Submission Packet

Status: `SUBMISSION_READY_EXCEPT_EXTERNAL_PROOF`

This document is a submission draft, not evidence that the hackathon entry has been filed.
Fields marked **REQUIRED PROOF** must be replaced with observed evidence before submission.

## Project

**RUMBO Verifiable Agent Control Plane × KeeperHub**

A fail-closed agent control plane that separates probabilistic intent from deterministic execution. RUMBO decides whether an action is authorized, KeeperHub executes the reviewed workflow, and the result is read back into a hash-bound evidence receipt before the action is treated as complete.

## Main-track fit

The integrated project is the existing public `verifiable-agent-control-plane` repository. It predates this integration and has a tagged `v0.2.0` release at commit `ed3bb2684743376fdf2769ee378ca614c913e3d4`. It is an installable Python reference implementation for fail-closed agent execution, deterministic revalidation, replay prevention, effect readback, and verifiable receipts.

Claim boundary: this is an existing released public project. This submission does **not** claim a particular user count, production deployment, KeeperHub endorsement, or prize acceptance.

## Problem

AI agents are probabilistic. Moving value is not. A model can choose the right action but still create unacceptable risk if authorization, execution, observed effect, and evidence drift apart.

RUMBO makes those states explicit:

`INTENT → AUTHORITY → PREFLIGHT → EXECUTION → READBACK → FALSIFICATION → RECEIPT`

KeeperHub becomes the deterministic execution boundary instead of asking the model to reinterpret value-moving instructions at execution time.

## Integration

The repository now contains a bounded KeeperHub adapter with these properties:

- public `GET /api/chains` connectivity discovery;
- authenticated workflow discovery via `GET /api/workflows`;
- explicit workflow execution via `POST /api/workflows/{workflowId}/execute`;
- one workflow-start budget per client instance;
- terminal readback via `/api/workflows/executions/{executionId}/wait`;
- SHA-256 request/response receipts;
- transport ambiguity fails closed instead of automatically replaying the POST;
- no direct on-chain broadcast method;
- direct-transfer helper produces the documented REST schema with `simulate: true` and `recipientAddress`.

The integration was audited against KeeperHub's current REST documentation after its first merge. That audit found and corrected a field-name mismatch (`toAddress` → `recipientAddress`) and strengthened replay protection for ambiguous network failures.

## Verification already complete

- KeeperHub integration PR #42 merged.
- Contract-audit fix PR #43 merged.
- Current audited repository head at packet creation: `ada5d9d125409488ff581a4c2308b9a4c4f291f3`.
- Full repository tests passed on Python 3.11, 3.12, and 3.13 before and after both promotions.
- Twin Bridge Verification passed before and after both promotions.
- Post-write readback confirmed only the expected files changed.

## KeeperHub surfaces used

For the final demo, use only the surfaces that are actually observed:

1. `GET /api/chains` — public service/network discovery.
2. `GET /api/workflows` — authenticated workflow discovery.
3. `POST /api/workflows/{workflowId}/execute` — exactly one explicitly authorized workflow start.
4. `GET /api/workflows/executions/{executionId}/wait` — terminal result readback.
5. `POST /api/execute/transfer` with `simulate: true` — optional direct-transfer preflight only.

Do not claim a surface was used merely because the adapter supports it.

## Network

Preferred demo network: **Base Sepolia (`84532`)**, only if the live `GET /api/chains` response reports it as both enabled and testnet at execution time.

Do not hard-code eligibility from this document. The demo must select from the live KeeperHub chain catalog.

## Required proof before DoraHacks submission

| Evidence | State | Value |
| --- | --- | --- |
| Public source repository | PASS | `https://github.com/fscfede-beep/verifiable-agent-control-plane` |
| Audited KeeperHub integration in `main` | PASS | `ada5d9d125409488ff581a4c2308b9a4c4f291f3` at packet creation |
| Python 3.11/3.12/3.13 CI | PASS | GitHub Actions |
| Twin Bridge Verification | PASS | GitHub Actions |
| KeeperHub organization credential validated | **REQUIRED PROOF** | `[INSERT — never paste the key]` |
| Owned/authorized workflow selected | **REQUIRED PROOF** | `[WORKFLOW ID / NAME]` |
| KeeperHub execution ID | **REQUIRED PROOF** | `[EXECUTION ID]` |
| Terminal workflow readback | **REQUIRED PROOF** | `[STATUS + RECEIPT HASH]` |
| KeeperHub transaction link | **REQUIRED PROOF** | `[TRANSACTION URL]` |
| Demo video | **REQUIRED PROOF** | `[VIDEO URL]` |
| DoraHacks BUIDL/submission URL | **REQUIRED PROOF** | `[SUBMISSION URL]` |

**Hard gate:** do not submit the main-track entry while the transaction link or demo video is missing. The hackathon brief requires source code, a short demo video, and proof of a transaction executed through KeeperHub.

## Suggested DoraHacks answers

### What did you build?

RUMBO Verifiable Agent Control Plane × KeeperHub connects an existing fail-closed agent reliability project to KeeperHub as its deterministic execution layer. An agent may propose an action, but execution only proceeds after explicit local authorization. The exact KeeperHub workflow is then invoked once, its terminal state is read back, and the observed request and response are bound into SHA-256 evidence receipts. Network ambiguity stops the client instead of silently retrying a potentially consequential action.

### What existing project is integrated?

`verifiable-agent-control-plane`, an existing public and installable Python reference project for fail-closed agent execution. Its `v0.2.0` release predates this KeeperHub integration. The KeeperHub work extends that project rather than creating a standalone wrapper solely for the hackathon.

### Why KeeperHub?

RUMBO intentionally does not reimplement transaction custody, workflow execution, gas handling, or settlement. KeeperHub is the external deterministic execution boundary. RUMBO contributes policy separation, explicit authorization, replay prevention, effect readback, and evidence reconciliation around that boundary.

### Reliability and observability

Every supported KeeperHub operation can generate a receipt containing the endpoint, canonical request SHA-256, response SHA-256, request ID when available, execution ID when available, and observed status. A workflow is not reported successful until KeeperHub returns a terminal successful readback. If the workflow-start transport becomes ambiguous, the client consumes its one-shot execution budget and refuses to resend automatically.

### Testnet or mainnet?

`[REPLACE WITH OBSERVED DEMO NETWORK]`.

For the planned demo, prefer an enabled KeeperHub testnet such as Base Sepolia, selected from the live chain catalog at run time. Do not claim mainnet use unless the final proof actually used mainnet.

### Unfinished parts / limitations

The repository integration and CI are complete. The external demo evidence is intentionally gated until a KeeperHub organization key is created and validated through the user's authorized account. The submission must not claim a live execution, transaction, or payout before those artifacts exist.

## Demo script — target under 3 minutes

**0:00–0:25 — Problem**
Show the control-plane state model and explain why an accepted agent action is not automatically safe to execute.

**0:25–0:45 — Existing project**
Show the repository and the pre-existing `v0.2.0` tag to establish that KeeperHub is integrated into an existing project.

**0:45–1:05 — Public KeeperHub discovery**
Run:

```bash
python examples/keeperhub_verified_execution.py
```

Show the live chain catalog receipt and the enabled testnet selected for the demo.

**1:05–1:30 — Fail-closed boundaries**
Show that private workflow discovery fails without `KEEPERHUB_API_KEY`, and explain that secrets never enter the receipt.

**1:30–2:05 — Real authorized execution**
With the key provided only through the environment, run:

```bash
python examples/keeperhub_verified_execution.py \
  --list-workflows \
  --execute-workflow YOUR_WORKFLOW_ID \
  --allow-execution \
  --wait
```

Show the returned `executionId`, final status, request hash, and response hash.

**2:05–2:35 — Transaction proof**
Open the actual transaction link produced through KeeperHub. If no transaction exists, stop: the main-track submission is not ready.

**2:35–2:55 — Reliability proof**
Show the Python 3.11/3.12/3.13 CI and Twin Bridge checks, plus the regression test that prevents automatic replay after an ambiguous workflow-start transport failure.

**2:55–3:00 — Close**
"Probabilistic agents decide. KeeperHub executes deterministically. RUMBO proves that the authorized action and observed effect still match."

## Final pre-submit checklist

- [x] Existing public project identified.
- [x] KeeperHub adapter merged to public repository.
- [x] REST contract audited against current KeeperHub docs.
- [x] Multi-version CI green.
- [x] Twin Bridge green.
- [ ] KeeperHub organization key created and validated.
- [ ] Owned/authorized workflow created or selected.
- [ ] Live `GET /api/chains` evidence captured.
- [ ] One bounded KeeperHub workflow execution completed.
- [ ] Terminal readback captured.
- [ ] Transaction link captured.
- [ ] Demo video recorded and uploaded.
- [ ] DoraHacks entry completed.
- [ ] Final URLs re-read after submission.

## Submission truth invariant

`CODE_PASS != LIVE_EXECUTION_PASS != SUBMISSION_PASS != PRIZE_PASS != CASH_RECEIVED`

Each state advances only when its own external evidence exists.
