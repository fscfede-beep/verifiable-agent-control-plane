# Evidence and claim boundary

## Verified on the publication candidate

- Python: 3.11.15
- `python -m py_compile src/verifiable_control_plane.py tests/test_control_plane.py`: PASS
- `python -m unittest discover -s tests -v`: 14/14 PASS
- dependency count for runtime/tests: 0 external Python packages
- production/reference implementation files containing private RUMBO bridge identifiers: 0
- external network calls in the implementation: 0
- credential reads: 0

## Verified on public GitHub Actions

- Workflow: `test`
- Publication baseline: `471cd3b07754dffd16d702f28674c3f3bc78983b`
- Run: https://github.com/fscfede-beep/verifiable-agent-control-plane/actions/runs/33769915677
- Matrix jobs: Python 3.11 / 3.12 / 3.13 — all `SUCCESS`
- In every matrix job, `python -m unittest discover -s tests -v` completed successfully.

This evidence applies to the public reference implementation and its test suite; it does not extend the claim boundary below.

## What the tests prove

The test suite proves the behavior of this small reference implementation:

- exact revision/checkpoint binding;
- stale-state rejection;
- duplicate-intent rejection;
- action allowlisting;
- secret-like payload-key rejection;
- read-only decision semantics;
- deterministic revalidation before effect execution;
- exactly-one-revision advancement;
- readback mismatch rejection;
- receipt hashing and receipt-chain binding;
- tamper detection;
- replay prevention.

## What is not proven

This repository does **not** prove:

- production deployment;
- distributed consensus;
- cryptographic signatures or hardware-backed keys;
- protection against every possible secret format;
- security certification;
- third-party penetration testing;
- OpenAI acceptance, endorsement, merge, employment, or affiliation;
- equivalence to any private production control plane.

The repository is deliberately narrow: a public, executable reference for separating model intent, authorization, execution, observed effect, receipt evidence, and state promotion.
