# Evidence and claim boundary

## Verified on the local 0.2.0 packaging candidate

- Python: 3.12.10
- `python -m pip wheel . --no-deps --wheel-dir dist`: PASS
- wheel: `verifiable_agent_control_plane-0.2.0-py3-none-any.whl`
- wheel SHA-256: `5BE1956BF565D4D1AF12CF15B2C335A9B321BDAAEA8BFE68CC8B4A5C749791BE`
- `python -m pip install .`: PASS
- `python -m unittest discover -s tests -v`: 16/16 PASS
- installed import from outside the repository checkout: PASS
- legacy `verifiable_control_plane` shim resolves to the same public API objects: PASS
- runtime dependency count: 0 external Python packages
- production/reference implementation files containing private RUMBO bridge identifiers: 0
- external network calls in the implementation: 0
- credential reads: 0

The build backend uses setuptools through the standard `[build-system]` interface. That is a build dependency, not a runtime dependency.

## Public GitHub Actions evidence

Published release `v0.1.0` is tagged at `848ceedbcb4e92ca2290f99b16e29421385f9b75`.

- release-tag workflow run: https://github.com/fscfede-beep/verifiable-agent-control-plane/actions/runs/33803306325
- Python 3.11 / 3.12 / 3.13 matrix: all `SUCCESS`

The 0.2.0 packaging changes must independently pass the same public matrix before promotion or release.

## What the tests prove

The test suite proves the behavior of this small reference implementation and its public import surface:

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
- replay prevention;
- installable public package import;
- legacy import compatibility.

## What is not proven

This repository does **not** prove:

- production deployment;
- distributed consensus;
- cryptographic signatures or hardware-backed keys;
- protection against every possible secret format;
- security certification;
- third-party penetration testing;
- PyPI publication;
- OpenAI acceptance, endorsement, merge, employment, or affiliation;
- equivalence to any private production control plane.

The repository is deliberately narrow: a public, executable reference for separating model intent, authorization, execution, observed effect, receipt evidence, and state promotion.
