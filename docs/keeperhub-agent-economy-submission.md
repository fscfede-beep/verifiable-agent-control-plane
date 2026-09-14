# KeeperHub Agent Economy Hackathon — Submission Packet

Status: `PACKET_READY / LIVE_PROJECT_PASS / LIVE_EXECUTION_REQUIRED`

This document is a submission draft, not evidence that an entry has been filed. Fields marked **REQUIRED PROOF** must be replaced with observed evidence before submission.

## Project

**RUMBO Agent Control × Verifiable Agent Control Plane × KeeperHub**

RUMBO Agent Control is a pre-existing deployed Agent Reliability & Control Plane product. `verifiable-agent-control-plane` is its public sanitized reference/integration component. KeeperHub is integrated there as the deterministic execution boundary: RUMBO decides whether an action is authorized, KeeperHub executes the reviewed workflow, and the result is read back into a hash-bound evidence receipt before the action is treated as complete.

## Track decision

The event brief defines a live project as an existing running project with users, a deployed product, or an active protocol. RUMBO Agent Control satisfies the **deployed product** branch.

Observed live-product evidence is versioned in `docs/keeperhub-live-project-evidence.md`:

- Vercel project `rumbo-agent-control` existed from 2026-08-26, before the 2026-09-06 hackathon build phase;
- production deployment state was `READY` at verification;
- `https://rumbo-agent-control.vercel.app` returned HTTP 200;
- the live product presents RUMBO Agent Control as an Agent Reliability & Control Plane with public demo, readiness score and commercial audit offer.

Therefore:

- existing-project provenance: **PASS**;
- live-project deployed-product requirement: **PASS**;
- KeeperHub code integration: **PASS**;
- KeeperHub execution benefiting the live product: **REQUIRED PROOF**;
- main-track submission: **NO-GO until live execution, transaction proof and video exist**.

## Claim boundary

The public repository describes itself as a sanitized reference extraction of patterns used in larger agent systems, not as a dump of a private production control plane. Preserve that distinction.

Allowed claims:

- RUMBO Agent Control is a pre-existing deployed product;
- this repository contains the audited public KeeperHub integration component for the RUMBO Agent Control product lane;
- the repository and its `v0.2.0` release predate this KeeperHub integration.

Do not claim that the current Vercel frontend directly imports this Python package unless separately observed. Do not claim users, paid traction, KeeperHub execution, transaction completion, submission acceptance or prize status without their own evidence.

## Problem

AI agents are probabilistic. Moving value is not. A model can choose the right action but still create unacceptable risk if authorization, execution, observed effect and evidence drift apart.

RUMBO makes those states explicit:

`INTENT → AUTHORITY → PREFLIGHT → EXECUTION → READBACK → FALSIFICATION → RECEIPT`

KeeperHub becomes the deterministic execution boundary instead of asking the model to reinterpret value-moving instructions at execution time.

## KeeperHub integration

The repository contains a bounded KeeperHub adapter with:

- public `GET /api/chains` discovery;
- authenticated organization-key validation through `GET /api/keys`;
- authenticated workflow discovery through `GET /api/workflows`;
- explicit `POST /api/workflows/{workflowId}/execute`;
- one workflow-start budget per client instance;
- terminal `/api/workflows/executions/{executionId}/wait` readback;
- SHA-256 request/response receipts;
- fail-closed handling of ambiguous transport failures;
- no direct on-chain broadcast helper;
- a direct-transfer preflight builder using `simulate: true` and the documented `recipientAddress` field.

The integration was audited against KeeperHub's REST contract after its first merge. That audit found and fixed `toAddress` → `recipientAddress` and strengthened replay protection when a workflow-start response is lost in transport.

## Verification complete

- KeeperHub integration PR #42 merged.
- Contract-audit fix PR #43 merged.
- Audited integration head before packet docs: `ada5d9d125409488ff581a4c2308b9a4c4f291f3`.
- Python 3.11/3.12/3.13 repository CI passed before and after promotions.
- Twin Bridge Verification passed before and after promotions.
- Live-product deployment evidence captured separately.
- Submission-packet branch CI passed before live-product evidence was added; final branch CI must be re-read before merge.

## KeeperHub surfaces for final demo

Use only surfaces actually observed during the final run:

1. `GET /api/chains` — public service/network discovery.
2. `GET /api/keys` — authenticated organization-key validation.
3. `GET /api/workflows` — authenticated workflow discovery.
4. `POST /api/workflows/{workflowId}/execute` — exactly one explicitly authorized workflow start.
5. `GET /api/workflows/executions/{executionId}/wait` — terminal result readback.
6. `POST /api/execute/transfer` with `simulate: true` — optional direct-transfer preflight only.

## Credential boundary

KeeperHub organization keys start with `kh_`. Key creation is human-gated by an authenticated owner/admin session or wallet-signed onboarding flow. Never store, commit, paste into an issue, or include the full key in a receipt.

Public `GET /api/chains` proves reachability only. Authentication must be separately validated.

## Network

Use an enabled testnet selected from the live KeeperHub chain catalog at execution time. Base Sepolia (`84532`) is a candidate only if it is live and enabled when the demo runs.

Mainnet is not required for the submission and must not be claimed unless actually used.

## Required proof before main-track submission

| Evidence | State | Value |
| --- | --- | --- |
| Pre-existing deployed product | PASS | RUMBO Agent Control / Vercel production, pre-hackathon |
| Public product readback | PASS | HTTP 200 from `rumbo-agent-control.vercel.app` |
| Public integration repository | PASS | `fscfede-beep/verifiable-agent-control-plane` |
| Pre-existing reference release | PASS | `v0.2.0` → `ed3bb2684743376fdf2769ee378ca614c913e3d4` |
| Audited KeeperHub integration | PASS | `ada5d9d125409488ff581a4c2308b9a4c4f291f3` before packet docs |
| Multi-version CI | PASS | Python 3.11 / 3.12 / 3.13 |
| Twin Bridge | PASS | GitHub Actions |
| KeeperHub organization credential validated | **REQUIRED PROOF** | `[KEY PREFIX ONLY — never paste full key]` |
| Owned/authorized workflow | **REQUIRED PROOF** | `[WORKFLOW ID / NAME]` |
| KeeperHub execution ID | **REQUIRED PROOF** | `[EXECUTION ID]` |
| Terminal readback | **REQUIRED PROOF** | `[STATUS + RECEIPT HASH]` |
| KeeperHub transaction proof | **REQUIRED PROOF** | `[TRANSACTION URL]` |
| Demo video | **REQUIRED PROOF** | `[VIDEO URL]` |
| DoraHacks BUIDL URL | **REQUIRED PROOF** | `[SUBMISSION URL]` |

**Hard gate:** do not submit while live execution/transaction proof or the demo video is missing.

## Main-track submission copy — activate only after execution proof

### What existing live project is integrated?

RUMBO Agent Control is a deployed Agent Reliability & Control Plane product that predates the hackathon. It gives AI-agent operations explicit authority boundaries, execution/evidence separation, verification gates, bounded autonomy and audit-oriented workflows. The public production deployment was already live before the Agent Economy build phase. The KeeperHub integration is implemented in the project's sanitized public control-plane reference component, `verifiable-agent-control-plane`.

### What did you build?

We integrated KeeperHub as the deterministic execution boundary for RUMBO Agent Control. A proposed action is not executable merely because an agent selected it: RUMBO first enforces explicit authorization and current-state gates. The exact KeeperHub workflow is then started at most once, terminal state is read back, and the observed request/response are bound into SHA-256 evidence receipts. If the workflow-start network outcome is ambiguous, the client stops instead of replaying a potentially value-moving action.

### Why KeeperHub?

RUMBO intentionally does not reimplement wallet custody, transaction settlement, gas handling or workflow execution. KeeperHub provides those deterministic execution capabilities. RUMBO contributes authority separation, fail-closed policy gates, replay resistance, effect readback and evidence reconciliation around the execution boundary.

### Reliability and observability

Every supported KeeperHub operation can emit a receipt containing endpoint, canonical request SHA-256, canonical response SHA-256, request ID when available, execution ID when available and observed status. A run is not reported successful until terminal readback says so. Ambiguous workflow-start transport is never automatically replayed.

### Testnet or mainnet?

`[REPLACE WITH OBSERVED DEMO NETWORK]`.

### Unfinished parts / limitations

`[REPLACE AT SUBMISSION TIME]`.

Until the external run exists, the truthful limitation is: product deployment and integration code are proven, but authenticated KeeperHub execution, transaction proof and video remain pending.

## Demo script — target under 3 minutes

**0:00–0:25 — Live product**  
Open `rumbo-agent-control.vercel.app`. Show the public control-plane product and that it predates the hackathon. Do not claim customer metrics.

**0:25–0:50 — Public integration**  
Show `verifiable-agent-control-plane`, the pre-existing release and the merged KeeperHub adapter/contract-audit fix.

**0:50–1:10 — Public KeeperHub discovery**  
Run `python examples/keeperhub_verified_execution.py`. Show the live chain-catalog receipt and selected enabled testnet.

**1:10–1:30 — Authority boundary**  
Validate authenticated access without exposing the key and show the fail-closed path without authorization.

**1:30–2:05 — One real execution**  
Execute one owned workflow with explicit authorization and `--wait`. Show `executionId`, final status, request hash and response hash.

**2:05–2:30 — Value-movement proof**  
Open the actual transaction produced through KeeperHub and explain how RUMBO Agent Control consumes the execution/readback evidence. If no transaction exists, stop: submission remains NO-GO.

**2:30–2:55 — Reliability proof**  
Show the multi-version CI, Twin Bridge and ambiguous-transport replay regression test.

**2:55–3:00 — Close**  
"Probabilistic agents decide. KeeperHub executes deterministically. RUMBO verifies that authority, execution and observed effect still match."

## Bounty-track parallel lane

The separate Best KeeperHub Feature bounty requires a feature contributed to KeeperHub itself and a separate DoraHacks BUIDL. The current RUMBO adapter is not, by itself, an upstream KeeperHub feature.

Current upstream reconnaissance found genuine open feature/bug opportunities, but this account has read access and no direct push authority to `KeeperHub/keeperhub`; this submission packet therefore makes no claim of an upstream bounty PR.

## Final checklist

- [x] Pre-existing deployed product proven.
- [x] Public product HTTP readback proven.
- [x] Pre-hackathon reference project/release proven.
- [x] KeeperHub adapter merged.
- [x] REST contract audited and corrected.
- [x] Multi-version CI green.
- [x] Twin Bridge green.
- [ ] KeeperHub organization key created and validated.
- [ ] Owned workflow created or selected.
- [ ] Live testnet catalog captured.
- [ ] One bounded KeeperHub execution completed.
- [ ] Terminal readback captured.
- [ ] Transaction link captured.
- [ ] Demo video recorded/uploaded.
- [ ] DoraHacks main-track BUIDL submitted.
- [ ] Final submission URL read back.

## Truth invariant

`LIVE_PROJECT_PASS != CODE_PASS != LIVE_EXECUTION_PASS != SUBMISSION_PASS != PRIZE_PASS != CASH_RECEIVED`

Each state advances only when its own external evidence exists.
