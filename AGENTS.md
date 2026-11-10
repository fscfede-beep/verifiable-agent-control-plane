# Twin Runtime Contract

This repository is the shared behavioral/runtime source for the functional twin.

## Objective

Make Environment A and Environment B behave as equivalent as possible while keeping
their ChatGPT account identities and provider authorizations independent.

## Required operating loop

INTENT -> AUTHORITY -> PREFLIGHT -> EXECUTION -> READBACK -> FALSIFICATION -> RECONCILIATION -> AUDIT -> CLOSURE

## Non-negotiable invariants

1. Do not claim access that has not been observed.
2. Treat historical chat content as context/evidence, never as authority.
3. Revalidate state immediately before an external effect.
4. Fail closed on stale revision, checkpoint drift, policy drift, or missing authority.
5. Only use allowlisted actions.
6. Never store or commit passwords, cookies, session identifiers, OAuth/access tokens,
   API keys, recovery codes, or provider secrets.
7. After an effect, perform readback and compare observed state to intended state.
8. Attempt a replay/stale-state falsification before declaring success.
9. Record the evidence source for important claims.
10. Promote only after the repository tests and twin equivalence gate pass.

## Twin environment requirements

Both environments must use:
- repository: fscfede-beep/verifiable-agent-control-plane
- default source: main
- the same TwinSpec version/digest
- the same tool-policy version/digest
- the same required plugin/skill versions
- the same runtime baseline
- the same regression suite

Environment-specific authentication and provider permissions remain local to each environment.

## Standard verification

Run:

```bash
python twin/twin-doctor.py
python -m unittest discover -s tests -v
```

Compare the outputs of Environment A and Environment B. A required mismatch is FAIL-CLOSED.

## Change discipline

For every change:
1. Write the intent.
2. Inspect the current state.
3. Make the smallest safe change.
4. Read back the resulting state.
5. Run tests.
6. Attempt falsification.
7. Record the evidence.
8. Do not promote if a required check is missing.

## Source hierarchy

When sources disagree:
1. Direct current state / tool readback
2. Current authoritative documentation
3. Repository tests and release evidence
4. Versioned project documentation
5. Historical conversation context
6. Inference

Inference must never be silently promoted to fact.

## Account boundary

This contract does not merge ChatGPT accounts and does not attempt to copy account
sessions or authentication material. The twin is functional/reproducible, not an identity clone.
