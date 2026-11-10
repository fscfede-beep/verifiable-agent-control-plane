---
name: audit-twin
description: Audit two functional twin environments and fail closed on state or policy drift.
---

Run this workflow:

1. Establish the intended twin objective.
2. Read the canonical TwinSpec and tool policy.
3. Compare repository revision, spec digest, tool-policy digest, runtime, and tests.
4. Revalidate immediately before any proposed effect.
5. Separate historical context from authority.
6. Require readback after every effect.
7. Attempt a replay/stale-state falsification.
8. Report PASS only when required evidence agrees.
9. Otherwise report FAIL-CLOSED with the exact divergence and evidence source.

Never request or store passwords, cookies, session identifiers, OAuth tokens, API keys, recovery codes, or other authentication material.
