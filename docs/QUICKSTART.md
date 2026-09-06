# Reliability Quickstart

This quickstart shows why an agent workflow is not successful merely because an action was requested or a tool returned without error.

The demo separates:

```text
INTENT -> AUTHORITY -> MATERIALIZATION -> READBACK -> RECEIPT -> VERIFICATION
```

It then intentionally reuses a stale decision after canonical state has advanced and proves the blocked target is not mutated.

## Prerequisites

- Python 3.11+
- A source checkout of this repository

## Install

```bash
python -m pip install .
```

## Run the demo

```bash
python examples/reliable_tool_workflow.py
```

A successful run exits with code `0` and includes both a verified PASS path and an expected FAIL-CLOSED path.
## Representative output

Receipt hashes are content-derived and are intentionally abbreviated here rather than treated as stable constants.

```text
PASS verified transition
  revision=0->1
  checkpoint=R1
  observed={'key': 'mode', 'value': 'safe'}
  receipt_sha256=<sha256...>
FAIL-CLOSED state drift after decision
  blocked_target_mutated=False
```

## What the PASS path proves

1. **INTENT** — the request binds to revision `0`, checkpoint `ZERO`, action `set_value`, and an exact payload.
2. **AUTHORITY / DECISION** — `decide(...)` evaluates the intent without mutating canonical state.
3. **MATERIALIZATION** — `materialize(...)` revalidates the decision against the current state before calling the target.
4. **READBACK** — the observed payload must equal the requested payload.
5. **RECEIPT** — the receipt binds the intent, prior state, next state, effect, and prior receipt hash.
6. **VERIFICATION** — `verify_transition(...)` checks the receipt and transition before the demo prints `PASS`.

The successful transition advances canonical state exactly once, from revision `0` to revision `1` / checkpoint `R1`.
## Why the stale decision fails closed

The second scenario creates a valid decision against revision `0`, then advances canonical state using a different accepted intent. The old decision is therefore bound to a state digest that is no longer current.

When the stale decision is presented for materialization, the control plane detects the mismatch and raises:

```text
state drift after decision
```

That check happens before the blocked target's `execute(...)` method is called. The demo verifies the blocked target remains empty and only then prints:

```text
FAIL-CLOSED state drift after decision
  blocked_target_mutated=False
```

This is the central reliability property demonstrated here: earlier authorization is not treated as timeless authorization after state changes.

## Next reading

- [`README.md`](../README.md) — project overview and core invariants
- [`CLAIMS.md`](../CLAIMS.md) — exact public claim boundaries and release evidence
- [`AGENT_SECURITY_THREAT_MODEL.md`](AGENT_SECURITY_THREAT_MODEL.md) — synthetic agent/tool security scenarios and non-goals

## Claim boundary

This repository is a public reference implementation. This quickstart is not evidence of a production deployment, enterprise scale, security certification, customer adoption, benchmark superiority, or complete agent-security coverage.

It does not imply OpenAI employment, endorsement, acceptance, or affiliation. The demo performs no external model/provider calls and uses synthetic in-memory targets only.
