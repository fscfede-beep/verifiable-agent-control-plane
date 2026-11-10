# An accepted agent action is not necessarily executable

A decision can be valid when it is made and unsafe by the time execution begins.

The core invariant in this reference implementation is:

`DECISION_ACCEPTED != EXECUTION_SAFE`

An accepted decision is evidence about a particular intent evaluated against a particular state. It is not a timeless capability token. If canonical state changes before materialization, the decision must be revalidated or rejected before the target can mutate.

This deep dive uses the executable state-drift path in [`examples/reliable_tool_workflow.py`](../examples/reliable_tool_workflow.py). It extends the [Reliability Quickstart](QUICKSTART.md); it does not introduce a second runtime path.

## The failure mode

Consider two actions that both start from revision `0`, checkpoint `ZERO`:

1. `quickstart-stale` is evaluated and accepted.
2. A different accepted intent executes first and advances canonical state to revision `1`.
3. The old decision is then presented for materialization against revision `1`.

The intent has not changed. The earlier decision has not been edited. What changed is the state the decision was bound to.

If execution trusted only `decision.accepted`, the stale action could run under assumptions that are no longer true.

## The pre-execution guard

`materialize()` verifies the decision against the current state before it invokes the supplied effect function:

```python
if not decision.accepted:
    raise ControlPlaneError("rejected decision cannot materialize")
if decision.intent_id != intent.intent_id or decision.intent_digest != intent.digest:
    raise ControlPlaneError("decision/intention binding mismatch")
if decision.state_digest != state.digest:
    raise ControlPlaneError("state drift after decision")

validate_intent(intent, state, policy)
effect = execute(intent.action, intent.payload)
```

The ordering matters. The state-digest comparison happens before `execute(...)`.

That makes the rejection observable as a pre-effect failure rather than as a compensating action after an unsafe mutation.

## Run the reproduction

From a source checkout:

```bash
python -m pip install .
python examples/reliable_tool_workflow.py
```

Representative output includes:

```text
PASS verified transition
  revision=0->1
  checkpoint=R1
  observed={'key': 'mode', 'value': 'safe'}
FAIL-CLOSED state drift after decision
  blocked_target_mutated=False
```

The exact receipt hash is content-derived, so this document does not treat one observed hash value as a universal constant.

The drift scenario is implemented by `run_state_drift_rejection()`:

- create and accept a decision at state `0`;
- advance canonical state with another valid transition;
- present the old accepted decision against the advanced state;
- require the exact rejection reason `state drift after decision`;
- inspect a fresh blocked target and require it to remain empty.

`blocked_target_mutated=False` is the key negative observation. The control plane did not merely report an error; the effect boundary was never crossed for the stale decision.

## Why receipt and readback still matter

There are two different proof shapes in the demo.

For the accepted path, execution occurs, observed payload is checked, and a receipt binds the intent, prior state, next state, effect, and previous receipt hash. `verify_transition()` then checks that evidence before promotion.

For the stale path, there should be no effect and therefore no success receipt. A receipt is not evidence that a blocked action was safe; the stronger property is that the stale action never reached the effect boundary.

This keeps three statements separate:

- **decision accepted** — the intent was valid against the earlier state;
- **effect observed** — an allowlisted execution actually produced the requested payload;
- **transition verified** — state and receipt evidence are internally consistent.

Collapsing those statements into a single `success=true` flag would erase the exact failure boundary this example is designed to expose.

## What this pattern generalizes to

The same race appears whenever authorization and execution are separated in time:

- a tool call is approved, then account or resource state changes;
- a deployment action is approved, then the target revision advances;
- an agent receives a grant, then delegation or policy changes;
- a workflow plans against one checkpoint while another actor commits first.

The implementation technique can vary. The invariant is stable: bind the decision to the state it evaluated, revalidate at the effect boundary, and fail closed when that binding no longer holds.

## Verification surface

This repository tests the same boundary directly in the core suite and through the executable quickstart. The documentation contract additionally checks that this deep dive keeps the runnable command, exact rejection reason, negative mutation observation, and claim boundaries visible.

See also:

- [Reliability Quickstart](QUICKSTART.md)
- [Agent Security Threat Model](AGENT_SECURITY_THREAT_MODEL.md)
- [`tests/test_control_plane.py`](../tests/test_control_plane.py)
- [`tests/test_reliable_tool_workflow.py`](../tests/test_reliable_tool_workflow.py)

## Claim boundary

This is a small public reference implementation and a controlled synthetic demonstration.

`REFERENCE_IMPLEMENTATION != PRODUCTION_SYSTEM`

It does not establish production deployment, enterprise-scale validation, complete security, certification, benchmark superiority, customer adoption, or OpenAI acceptance, employment, endorsement, or affiliation.
