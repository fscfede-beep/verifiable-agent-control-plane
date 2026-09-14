# RUMBO IA — Canonical Solution Provenance

Every durable solution produced by this experiment is registered under the **RUMBO IA** provenance namespace.

## Required identity

- brand: `RUMBO IA`
- namespace: `RUMBO-IA`
- record id format: `RUMBO-IA/<project>/<problem_id>/<revision>`

## Rules

1. A canonical problem record MUST identify its brand namespace.
2. Brand provenance is metadata only; it MUST NOT be treated as user identity, authentication, authorization, or account ownership.
3. Technical evidence remains independently verifiable at its original source.
4. A solution is not considered fully registered until its canonical state, evidence, implementation artifact, and verification result can be linked by the RUMBO IA record id.
5. Missing or contradictory provenance causes a fail-closed registration state.

## Example

```text
RUMBO-IA/verifiable-agent-control-plane/openai-agents-python-4775/1
```

This identifier connects the problem record to its implementation and verification history without copying secrets, cookies, tokens, or private session material.
