# RUMBO IA — 90-Second Agent State-Drift Video Package

Target channel: `RUMBO IA / @RumboAGI`

Source evidence:
- `docs/STATE_DRIFT_AFTER_DECISION.md`
- `docs/QUICKSTART.md`
- `CLAIMS.md`
- `examples/reliable_tool_workflow.py`

Publishing state: NOT_PUBLISHED

## 90-second script

An agent action can be accepted and still be unsafe to execute.

In this Python reference implementation, a decision is accepted against revision zero. Then another valid action advances canonical state to revision one. If we treated `accepted=true` like a timeless capability, the stale action could run under assumptions that are no longer true.

The guard is deliberately before the effect boundary. The state digest is checked before `execute(...)`. If it no longer matches, materialization raises `state drift after decision`.

Run the demo and you see the normal path first:

`PASS verified transition`

Then the stale decision is replayed:

`FAIL-CLOSED state drift after decision`

And the key negative observation is:

`blocked_target_mutated=False`

That last line matters more than an error message. The blocked action never reached the effect function.

The invariant is:

`DECISION_ACCEPTED != EXECUTION_SAFE`

Bind a decision to the state it evaluated, revalidate at the effect boundary, and fail closed when that binding is stale.

This is a controlled public reference implementation, not a production deployment or certification:

`REFERENCE_IMPLEMENTATION != PRODUCTION_SYSTEM`

## Shot list

| Time | Visual | On-screen text / action |
| --- | --- | --- |
| 0:00–0:08 | Tight crop on terminal + title card | `DECISION_ACCEPTED != EXECUTION_SAFE` |
| 0:08–0:22 | Show `STATE_DRIFT_AFTER_DECISION.md` failure sequence | decision at revision `0` → canonical state advances to `1` |
| 0:22–0:34 | Show the guard in `materialize()` | state digest check occurs before `execute(...)` |
| 0:34–0:48 | Terminal: run demo | `python examples/reliable_tool_workflow.py` |
| 0:48–0:58 | Freeze on accepted path | `PASS verified transition` |
| 0:58–1:12 | Freeze on stale path | `FAIL-CLOSED state drift after decision` |
| 1:12–1:20 | Highlight negative observation | `blocked_target_mutated=False` |
| 1:20–1:30 | Closing card | `REFERENCE_IMPLEMENTATION != PRODUCTION_SYSTEM` + repo URL |

Production note: use the actual terminal output from the recorded run. Do not substitute a fabricated receipt hash or claim a result that was not observed.

## YouTube metadata

**Title:** An Accepted Agent Action Is Not Necessarily Executable

**Description:**

A 90-second walkthrough of a state-drift failure boundary in a small public Python agent-control reference implementation.

The decision is valid when accepted, canonical state changes before execution, and materialization revalidates the state binding before the effect boundary. The stale action is rejected with `state drift after decision`, and the blocked target remains unchanged: `blocked_target_mutated=False`.

Core invariant: `DECISION_ACCEPTED != EXECUTION_SAFE`.

Repository: https://github.com/fscfede-beep/verifiable-agent-control-plane
Deep dive: `docs/STATE_DRIFT_AFTER_DECISION.md`
Quickstart: `docs/QUICKSTART.md`

Boundary: controlled reference implementation, not production deployment, enterprise validation, security certification, benchmark superiority, customer adoption, or OpenAI employment/endorsement/affiliation.

**Chapters:**
- `0:00` The stale-decision race
- `0:22` Pre-effect state revalidation
- `0:34` Run the demo
- `0:58` Fail closed
- `1:20` Claim boundary

## LinkedIn copy

A decision can be correct when an agent makes it and stale when execution begins.

I put together a short executable example of that boundary: accept an action against one canonical state, advance the state, then try to materialize the old decision. The guard revalidates before the effect function, rejects with `state drift after decision`, and the blocked target remains unchanged: `blocked_target_mutated=False`.

`DECISION_ACCEPTED != EXECUTION_SAFE`

Small public Python reference implementation; controlled demonstration, not a production or certification claim.

Repo: https://github.com/fscfede-beep/verifiable-agent-control-plane

## X copy

Accepted does not mean executable.

Bind the decision to the state it evaluated. Revalidate before the effect boundary. On drift: fail closed.

`blocked_target_mutated=False`

`DECISION_ACCEPTED != EXECUTION_SAFE`

https://github.com/fscfede-beep/verifiable-agent-control-plane

## Claim audit

Grounded by the current deep dive and claim boundary:
- accepted decision is bound to a particular prior state;
- state drift is rejected before `execute(...)`;
- the executable demo exposes `FAIL-CLOSED state drift after decision`;
- `blocked_target_mutated=False` is the negative observation;
- no production, certification, customer-adoption, benchmark-superiority, OpenAI acceptance, employment, endorsement, or affiliation claim is made.

Publishing or recording this package is a separate external action.
