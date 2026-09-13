# KeeperHub Agent Economy Hackathon — Submission Packet

Status: `PACKET_READY / MAIN_TRACK_ELIGIBILITY_NOT_PROVEN / EXTERNAL_PROOF_REQUIRED`

This document is a submission draft, not evidence that an entry has been filed. Fields marked **REQUIRED PROOF** must be replaced with observed evidence before submission.

## Project

**RUMBO Verifiable Agent Control Plane × KeeperHub**

A fail-closed agent control plane that separates probabilistic intent from deterministic execution. RUMBO decides whether an action is authorized, KeeperHub executes the reviewed workflow, and the result is read back into a hash-bound evidence receipt before the action is treated as complete.

## Track decision

The current integration is technically strong but main-track eligibility is not yet proven.

The event brief defines a "live project" as a project that exists and is running, with users, a deployed product, or an active protocol behind it. The public `verifiable-agent-control-plane` repository predates the hackathon and has a tagged `v0.2.0` release, but a public repository/release alone is not evidence of users, a deployed product, or an active protocol.

Therefore:

- existing-project provenance: **PASS**;
- KeeperHub integration in that project: **PASS**;
- live-project requirement: **NOT_PROVEN**;
- main-track submission: **FAIL-CLOSED until live-project evidence exists**.

Do not describe the repository as a qualifying "live project" unless a deployed/running product, real users, or an active protocol can be evidenced.

## Existing-project provenance

The integrated project is the existing public `verifiable-agent-control-plane` repository. It predates this integration and has a tagged `v0.2.0` release at commit `ed3bb2684743376fdf2769ee378ca614c913e3d4`. It is an installable Python reference implementation for fail-closed agent execution, deterministic revalidation, replay prevention, effect readback, and verifiable receipts.

Claim boundary: this proves the project existed before the KeeperHub work. It does **not** by itself prove main-track live-project eligibility, production usage, user count, KeeperHub endorsement, submission acceptance, or prize eligibility.

## Problem

AI agents are probabilistic. Moving value is not. A model can choose the right action but still create unacceptable risk if authorization, execution, observed effect, and evidence drift apart.

RUMBO makes those states explicit:

`INTENT → AUTHORITY → PREFLIGHT → EXECUTION → READBACK → FALSIFICATION → RECEIPT`

KeeperHub becomes the deterministic execution boundary instead of asking the model to reinterpret value-moving instructions at execution time.

## Integration

The repository contains a bounded KeeperHub adapter with these properties:

- public `GET /api/chains` connectivity discovery;
- credential validation can use authenticated `GET /api/keys`;
- authenticated workflow discovery via `GET /api/workflows`;
- explicit workflow execution via `POST /api/workflows/{workflowId}/execute`;
- one workflow-start budget per client instance;
- terminal readback via `/api/workflows/executions/{executionId}/wait`;
- SHA-256 request/response receipts;
- transport ambiguity fails closed instead of automatically replaying the POST;
- no direct on-chain broadcast method;
- direct-transfer helper produces the documented REST schema with `simulate: true` and `recipientAddress`.

The integration was audited against KeeperHub's REST documentation after its first merge. That audit found and corrected a field-name mismatch (`toAddress` → `recipientAddress`) and strengthened replay protection for ambiguous network failures.

## Verification already complete

- KeeperHub integration PR #42 merged.
- Contract-audit fix PR #43 merged.
- Audited repository head before this packet branch: `ada5d9d125409488ff581a4c2308b9a4c4f291f3`.
- Full repository tests passed on Python 3.11, 3.12, and 3.13 before and after both promotions.
- Twin Bridge Verification passed before and after both promotions.
- Post-write readback confirmed only expected files changed.
- Initial submission-packet branch CI passed.

## KeeperHub surfaces for the final demo

Use only surfaces actually observed during the final run:

1. `GET /api/chains` — public service/network discovery.
2. `GET /api/keys` — authenticated organization-key validation.
3. `GET /api/workflows` — authenticated workflow discovery.
4. `POST /api/workflows/{workflowId}/execute` — exactly one explicitly authorized workflow start.
5. `GET /api/workflows/executions/{executionId}/wait` — terminal result readback.
6. `POST /api/execute/transfer` with `simulate: true` — optional direct-transfer preflight only.

Do not claim a surface was used merely because the adapter supports it.

## Credential boundary

KeeperHub organization keys start with `kh_`. Key creation is intentionally human-gated: normal signup uses browser authentication and organization-key creation requires an owner/admin session; headless onboarding still requires a wallet-controlled SIWE/signature confirmation. Never store, commit, paste into an issue, or include the full key in a receipt.

A valid key should be confirmed through authenticated `GET /api/keys`; public `GET /api/chains` proves reachability only, not authentication.

## Network

Preferred demo network: an enabled testnet selected from the live `GET /api/chains` response at execution time. Base Sepolia (`84532`) is only a candidate, not a hard-coded eligibility fact.

Do not claim mainnet use unless the final proof actually used mainnet.

## Required proof before a main-track submission

| Evidence | State | Value |
| --- | --- | --- |
| Public source repository | PASS | `https://github.com/fscfede-beep/verifiable-agent-control-plane` |
| Pre-existing project provenance | PASS | `v0.2.0` → `ed3bb2684743376fdf2769ee378ca614c913e3d4` |
| Audited KeeperHub integration in `main` | PASS | `ada5d9d125409488ff581a4c2308b9a4c4f291f3` before packet docs |
| Python 3.11/3.12/3.13 CI | PASS | GitHub Actions |
| Twin Bridge Verification | PASS | GitHub Actions |
| Qualifying live-project evidence | **REQUIRED PROOF** | `[DEPLOYMENT / USERS / ACTIVE PROTOCOL EVIDENCE]` |
| KeeperHub organization credential validated | **REQUIRED PROOF** | `[KEY PREFIX ONLY — never paste full key]` |
| Owned/authorized workflow selected | **REQUIRED PROOF** | `[WORKFLOW ID / NAME]` |
| KeeperHub execution ID | **REQUIRED PROOF** | `[EXECUTION ID]` |
| Terminal workflow readback | **REQUIRED PROOF** | `[STATUS + RECEIPT HASH]` |
| KeeperHub transaction link | **REQUIRED PROOF** | `[TRANSACTION URL]` |
| Demo video | **REQUIRED PROOF** | `[VIDEO URL]` |
| DoraHacks BUIDL/submission URL | **REQUIRED PROOF** | `[SUBMISSION URL]` |

**Hard gate:** do not submit to the main track while live-project evidence, transaction proof, or demo video is missing.

## Main-track submission copy — use only after gates pass

### What did you build?

RUMBO Verifiable Agent Control Plane × KeeperHub connects an existing fail-closed agent reliability project to KeeperHub as its deterministic execution layer. An agent may propose an action, but execution only proceeds after explicit authorization. The exact KeeperHub workflow is then invoked once, its terminal state is read back, and the observed request and response are bound into SHA-256 evidence receipts. Network ambiguity stops the client instead of silently retrying a potentially consequential action.

### What existing project is integrated?

`[REPLACE WITH VERIFIED LIVE-PROJECT DESCRIPTION]`.

The codebase is `verifiable-agent-control-plane`, an existing public and installable Python project whose `v0.2.0` release predates this KeeperHub integration. Do not state that this alone satisfies the event's live-project requirement.

### Why KeeperHub?

RUMBO intentionally does not reimplement transaction custody, workflow execution, gas handling, or settlement. KeeperHub is the external deterministic execution boundary. RUMBO contributes policy separation, explicit authorization, replay prevention, effect readback, and evidence reconciliation around that boundary.

### Reliability and observability

Every supported KeeperHub operation can generate a receipt containing the endpoint, canonical request SHA-256, response SHA-256, request ID when available, execution ID when available, and observed status. A workflow is not reported successful until KeeperHub returns a terminal successful readback. If the workflow-start transport becomes ambiguous, the client consumes its one-shot execution budget and refuses to resend automatically.

### Testnet or mainnet?

`[REPLACE WITH OBSERVED DEMO NETWORK]`.

### Unfinished parts / limitations

`[REPLACE AT SUBMISSION TIME]`.

Current truthful state: repository integration and CI are complete; live-project eligibility, KeeperHub account authorization, live execution, transaction proof, and demo video remain externally gated.

## Demo script — target under 3 minutes

**0:00–0:25 — Problem**  
Show the control-plane state model and explain why an accepted agent action is not automatically safe to execute.

**0:25–0:45 — Existing project**  
Show the repository and pre-existing `v0.2.0` tag. Separately show the evidence that makes the integrated project "live" under the event definition. If that evidence does not exist, stop and do not represent the main-track gate as passed.

**0:45–1:05 — Public KeeperHub discovery**  
Run `python examples/keeperhub_verified_execution.py` and show the live chain-catalog receipt.

**1:05–1:30 — Authentication and fail-closed boundaries**  
Validate the `kh_` credential without exposing it, show the key prefix only, and demonstrate that private operations fail without authorization.

**1:30–2:05 — Real authorized execution**  
Run the owned workflow once with explicit authorization and `--wait`. Show `executionId`, final status, request hash, and response hash.

**2:05–2:35 — Transaction proof**  
Open the actual transaction link produced through KeeperHub. If no transaction exists, stop: the main-track submission is not ready.

**2:35–2:55 — Reliability proof**  
Show Python 3.11/3.12/3.13 CI, Twin Bridge, and the regression test preventing replay after an ambiguous workflow-start transport failure.

**2:55–3:00 — Close**  
"Probabilistic agents decide. KeeperHub executes deterministically. RUMBO proves that the authorized action and observed effect still match."

## Bounty-track fallback / parallel lane

The event also offers a separate KeeperHub feature bounty. It requires a feature contributed as a pull request to KeeperHub itself and is judged on mergeability, platform value, code quality/tests, scope, and completeness. Examples named by the organizers include chain integrations, nodes, triggers/actions, connectors, and developer-experience improvements.

This current RUMBO adapter does **not** qualify for that bounty merely because it integrates KeeperHub in this repository. A separate upstream KeeperHub PR/BUIDL is required. The bounty can stack economically with the main track, but DoraHacks requires separate BUIDLs for the two tracks.

## Final pre-submit checklist

- [x] Existing public project identified.
- [x] Pre-hackathon release evidence identified.
- [x] KeeperHub adapter merged to public repository.
- [x] REST contract audited against current KeeperHub docs.
- [x] Multi-version CI green.
- [x] Twin Bridge green.
- [ ] Live-project requirement proven with deployment/users/active-protocol evidence.
- [ ] KeeperHub organization key created and validated.
- [ ] Owned/authorized workflow created or selected.
- [ ] Live chain-catalog evidence captured.
- [ ] One bounded KeeperHub workflow execution completed.
- [ ] Terminal readback captured.
- [ ] Transaction link captured.
- [ ] Demo video recorded and uploaded.
- [ ] DoraHacks main-track entry completed.
- [ ] Final URLs re-read after submission.

## Submission truth invariant

`EXISTING_PROJECT_PASS != LIVE_PROJECT_PASS != CODE_PASS != LIVE_EXECUTION_PASS != SUBMISSION_PASS != PRIZE_PASS != CASH_RECEIVED`

Each state advances only when its own external evidence exists.
