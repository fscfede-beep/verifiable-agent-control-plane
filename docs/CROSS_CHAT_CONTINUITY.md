# Canonical Cross-Chat Continuity Protocol

## Purpose

A new chat must be able to continue work without requiring the original conversation transcript.

The transportable unit is a **canonical problem state**, not a chat transcript.

## State machine

```
DISCOVER
  -> EVIDENCE
  -> RECONCILE
  -> SOLVE
  -> VERIFY
  -> RECORD
  -> RESUME
```

A transition may move to `FAIL_CLOSED` whenever required evidence is missing, stale,
ambiguous, or contradictory.

## Canonical state contract

Every durable problem record MUST contain:

- `schema_version`
- `problem_id`
- `title`
- `objective`
- `status`
- `revision`
- `created_at`
- `updated_at`
- `evidence`
- `decisions`
- `artifacts`
- `verification`
- `next_actions`

### Identity rules

`problem_id` is stable across chats.

`revision` increases monotonically and changes whenever the canonical state changes.

A chat identifier, user session, browser cookie, access token, or provider-specific
session identifier MUST NOT be used as the canonical identity of the problem.

## Evidence rules

Each evidence item MUST declare:

- `source`
- `kind`
- `locator`
- `observed_at`
- `digest`
- `status`

Evidence statuses are:

- `verified`
- `stale`
- `contradictory`
- `unavailable`

Only `verified` evidence may support a PASS transition.

## Resolution rules

A solution is not considered complete merely because a proposal exists.

Required sequence:

1. reconstruct the problem from durable evidence;
2. identify the current state;
3. reconcile conflicting observations;
4. produce the smallest sufficient change;
5. verify the resulting state;
6. record the verification and resulting revision.

If steps 1-5 cannot be established, the system MUST return `FAIL_CLOSED` rather than
inventing missing context.

## Cross-chat resume

A new chat resumes work by searching for `problem_id` and reading the latest revision.

The resume operation MUST return:

- canonical objective;
- latest verified revision;
- unresolved risks;
- completed verification;
- exact next action;
- links/locators for durable artifacts.

The original chat transcript is optional.

## Security and privacy boundary

Canonical state MUST NOT contain:

- passwords;
- API keys;
- cookies;
- bearer tokens;
- private session identifiers;
- authentication material.

It MAY contain public repository names, issue/PR numbers, commit hashes, file paths,
test results, and sanitized operational evidence.

## Success criterion

The experiment succeeds when a fresh chat can reconstruct the same actionable state from
the canonical record, reach the same safe decision, and continue without relying on hidden
conversation context.

## Example

```json
{
  "schema_version": "1.0",
  "problem_id": "openai-agents-python/4775",
  "title": "Pending-input Session append duplication",
  "objective": "Prevent duplicate logical input after a lost Session.add_items acknowledgement",
  "status": "VERIFIED_PENDING_EXTERNAL_GATE",
  "revision": 4,
  "evidence": [
    {
      "source": "github",
      "kind": "pull_request",
      "locator": "openai/openai-agents-python#4906",
      "observed_at": "2026-09-08T06:53:00Z",
      "digest": "sha256:b377972dfc7d3154e6a11596b1bb0397decfc1ab",
      "status": "verified"
    }
  ],
  "decisions": [
    "Use fail-closed checkpoint/reconciliation instead of blind retry"
  ],
  "artifacts": [
    {
      "kind": "commit",
      "locator": "b377972dfc7d3154e6a11596b1bb0397decfc1ab"
    }
  ],
  "verification": {
    "code_audit": "pass",
    "regression_scope": "pass",
    "external_ci_gate": "action_required"
  },
  "next_actions": [
    "Approve/re-run the GitHub Actions workflow and perform final maintainer review"
  ]
}
```
