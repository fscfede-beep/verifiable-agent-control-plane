# RUMBO IA — Agent Reliability Quickstart Video Script

Target channel: `RUMBO IA / @RumboAGI`

## Opening

Agent systems often collapse several different facts into one word: success. A model proposed an action, a policy allowed it, a tool ran, and the system assumes the intended effect happened. This quickstart keeps those facts separate and verifies the effect before reporting success.

On screen, show the repository and this sequence:

```text
INTENT -> AUTHORITY -> MATERIALIZATION -> READBACK -> RECEIPT -> VERIFICATION
```

State clearly: this is a public Python reference implementation using synthetic in-memory targets.

## Install and run

Show exactly:

```bash
python -m pip install .
python examples/reliable_tool_workflow.py
```

Explain that the example uses only the package's public import surface and no external model, provider, database, credential, or network call.
## PASS walkthrough

Pause on:

```text
PASS verified transition
  revision=0->1
  checkpoint=R1
  observed={'key': 'mode', 'value': 'safe'}
  receipt_sha256=<actual hash from the run>
```

Explain:
- the intent is bound to revision `0` and checkpoint `ZERO`;
- the decision phase is read-only;
- materialization revalidates before execution;
- readback must match the requested payload;
- the receipt binds the transition and observed effect;
- `PASS` is printed only after `verify_transition(...)` succeeds.

Do not present the shown receipt hash as a universal constant; it is evidence from that run.

## Intentional state-drift failure

Then show:

```text
FAIL-CLOSED state drift after decision
  blocked_target_mutated=False
```

Explain that a decision valid against revision `0` is intentionally reused after canonical state advances. Because the state digest changed, execution is rejected before the blocked target can mutate.
## Closing

The key idea is not that failures disappear. It is that authority, execution, observed effect, and evidence stay distinguishable when state changes or a tool behaves unexpectedly.

Closing boundary, read verbatim:

> This is a public reference implementation and controlled demonstration. It is not a production certification, enterprise-scale validation, security certification, customer-adoption claim, or benchmark claim. It does not imply OpenAI employment, endorsement, acceptance, or affiliation.

Point viewers to:
- `docs/QUICKSTART.md`
- `CLAIMS.md`
- `docs/AGENT_SECURITY_THREAT_MODEL.md`

Publishing or recording the video is a separate action from this repository change.
