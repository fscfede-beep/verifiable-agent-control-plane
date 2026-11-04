# RUMBO Voice Recovery Agent — CALL-E adapter

A dry-run-first proof of concept that connects a bounded RUMBO lead-recovery workflow to the official CALL-E Python SDK.

The adapter is intentionally fail-closed. It can preview the exact outbound task and schemas without placing a call. A real call requires an authorized E.164 recipient, a server-side `CALLE_API_KEY`, the `--live` flag, and the exact confirmation string `PLACE CALL`.

## Use case

Small businesses lose revenue when leads go stale, appointments become no-shows, or missed calls are not recovered. This example turns one approved recovery item into a bounded CALL-E phone task and returns structured data that can be reviewed before any follow-up action.

The result schema is restricted to:

- contact status;
- intent;
- proposed next action;
- optional preferred time;
- optional notes.

No downstream action is executed automatically.

## Safety model

- Dry-run is the default.
- A live call requires **both** `--live` and `--confirm "PLACE CALL"`.
- The CALL-E API key is read only from `CALLE_API_KEY` and is never printed.
- The recipient phone number is never printed in output; a SHA-256 fingerprint is emitted instead.
- The task forbids passwords, one-time codes, payment-card data, financial secrets, medical information, and legal advice.
- Result schemas use `additionalProperties: false`.
- Every consequential next action remains human-approved.
- Use only an authorized recipient number and comply with applicable consent/calling rules.

## Requirements

- Python 3.11+
- `calle-ai==0.7.0`

Install:

```bash
python -m pip install -r requirements.txt
```

## Dry run — no phone call

Use a standards-reserved fictional number for previewing:

```bash
python app.py --phone +14155550123 --workflow-id lead-demo-123
```

The command prints a redacted plan, idempotency key, safety flags, and result schemas. It does **not** contact CALL-E.

## Live verification

Only after selecting an authorized recipient:

```bash
export CALLE_API_KEY="..."
python app.py \
  --phone <AUTHORIZED_E164_PHONE> \
  --workflow-id <DURABLE_WORKFLOW_ID> \
  --live \
  --confirm "PLACE CALL"
```

The live path calls `CalleClient.calls.create_and_wait(...)` with:

- E.164 recipient;
- explicit region and locale;
- bounded task text;
- top-level and recipient structured-result schemas;
- workflow metadata;
- durable idempotency key.

The adapter prints the CALL-E call id, terminal status, structured results, provider evidence, and a phone fingerprint. It does not execute the proposed next action.

## Tests

```bash
python -m unittest -v test_app.py
```

The tests cover:

1. E.164 validation;
2. rejection of malformed phone numbers;
3. stable idempotency for the same workflow;
4. idempotency separation across workflows;
5. phone-number redaction;
6. bounded next-action schema.

## Side effects and cancellation

Dry-run mode has no external side effect. Live mode can place one real outbound phone call through CALL-E. There is no recurring schedule in this example, so cancellation means not entering live mode. If a live call has already been created, provider-side CALL-E controls are authoritative for its lifecycle.

## Evidence and status

Current implementation status:

- local adapter tests: **6/6 PASS** in the originating RUMBO workstream;
- public branch: implementation source published for review;
- live CALL-E call: **NOT EXECUTED** in this repository state;
- cash/prize claim: **NONE**;
- consequential follow-up: **HUMAN APPROVAL REQUIRED**.

Do not claim a working live integration until at least one authorized CALL-E runtime call succeeds and its returned structured result is captured.

## CALL-E hackathon fit

This example is designed as a reusable Python app / adapter contribution. The current CALL-E hackathon requires a functional project, a public pull request to `CALLE-AI/awesome-phone-call-agents`, a public demo video, and the CALL-E account email on Devpost. A live runtime use of CALL-E should be demonstrated before claiming completion.
