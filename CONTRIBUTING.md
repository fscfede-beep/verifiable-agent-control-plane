# Contributing

Thanks for helping improve this reference implementation.

## Scope

Contributions should strengthen the public control-plane reference without expanding its claims beyond what can be tested here.

Good contributions include:
- bug fixes for decision/materialization/readback/receipt behavior;
- regression tests for stale state, replay, tampering, packaging, or fail-closed boundaries;
- clearer documentation of verified behavior and claim limits;
- CI or developer-experience improvements that preserve the runtime-dependency-free package.

Out of scope without prior discussion:
- production deployment configuration or private RUMBO state;
- credentials or provider-specific secrets;
- claims of certification, endorsement, or production readiness;
- broad feature additions that obscure the small reference model.

## Before opening a pull request

1. Run `python -m pip install .` from a clean environment.
2. Run `python -m unittest discover -s tests -v`.
3. Verify both `import verifiable_agent_control_plane` and the legacy compatibility import `import verifiable_control_plane` outside the checkout.
4. Run `git diff --check`.
5. Update `CLAIMS.md` if the evidence boundary changes.

Security issues should be reported privately through the Security tab, not through a public issue.