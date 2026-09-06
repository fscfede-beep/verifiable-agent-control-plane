# RUMBO Agent Reliability Quickstart — Design

Date: 2026-09-05

**Target base:** `fscfede-beep/verifiable-agent-control-plane`

**Verified base SHA:** `7efcef7ee68eaa2f5a422f5b509fa5725dcc4785`

**Goal:** turn the existing reference control plane into a developer-facing quickstart that a new developer can clone, run, understand, and falsify in under 10 minutes without weakening the repository's existing reliability or claim boundaries.

## Why this change

The repository already exposes a small, dependency-free Python API for intent validation, fail-closed materialization, effect readback, hash-bound receipts, and transition verification. It also has a public Python 3.11/3.12/3.13 test matrix.

The missing developer-experience layer is a guided path from clone to observed behavior. The quickstart will make the existing engineering easier to consume without creating a new product, service, or Portfolio root.

## Success criteria

1. A developer can clone the repository, install from source, and run one command to execute the demo.
2. The demo shows one accepted transition and one deterministic fail-closed transition.
3. The accepted path visibly separates intent, decision, execution, readback, receipt, and verification.
4. The rejected path proves that stale state cannot materialize an effect.
5. All examples use only the repository's public import surface.
6. The complete existing unit suite remains green on Python 3.11, 3.12, and 3.13.
7. Documentation never upgrades the project from reference implementation to production system.

## Non-goals

- No external API, LLM, MCP server, browser automation, database, network call, or credential is introduced.
- No change to the core or security public API is planned.
- No production deployment, enterprise validation, security certification, or OpenAI affiliation is claimed.
- No new package dependency is added solely for the demo.
- No separate repository or Portfolio root is created.
- No interactive web UI is required for this slice.

## Developer journey

The primary path is deliberately linear:

```text
git clone
  -> python -m pip install .
  -> python examples/reliable_tool_workflow.py
  -> observe PASS transition
  -> observe FAIL-CLOSED stale-state rejection
  -> inspect receipt / state output
  -> read docs/QUICKSTART.md for the invariant mapping
```

The quickstart must work from a clean source checkout after installation and must not depend on the current working directory being importable as a package.

## Files and responsibilities

### `examples/reliable_tool_workflow.py`
A standalone executable example using only `verifiable_agent_control_plane` public imports.

The example contains two named scenarios and a `main()` entry point.

**Scenario A — verified transition**
- start from `CanonicalState()`;
- create an intent bound to revision `0` and checkpoint `ZERO`;
- allow only `set_value` in `Policy`;
- call `decide`, then `materialize` through `InMemoryTarget.execute`;
- call `verify_transition` before reporting success;
- print stable, human-readable evidence: decision status, revision change, checkpoint, observed payload, and receipt hash.

**Scenario B — state drift fails closed**
- create a second intent and decision against the same initial state;
- advance canonical state with a different accepted intent;
- attempt to materialize the previously accepted decision against the advanced state;
- require `ControlPlaneError("state drift after decision")`;
- prove the target for the blocked action did not mutate.

The script returns exit code `0` only when both the verified PASS and the expected fail-closed rejection occur. An unexpected acceptance, unexpected exception type/message, or failed transition verification returns non-zero.

### `tests/test_reliable_tool_workflow.py`
Tests the example as a developer-facing contract rather than duplicating core internals.

Required tests:
1. PASS scenario reaches revision 1 and verifies the transition.
2. Drift scenario raises the expected fail-closed error before target mutation.
3. `main()` returns `0` and emits both `PASS` and `FAIL-CLOSED` markers.
4. The example imports only from the public package surface, enforced by code review plus installed-package execution in CI.

### `docs/QUICKSTART.md`
A short tutorial optimized for first-run comprehension.

Structure:
- what problem the demo illustrates;
- prerequisites: Python 3.11+ and a source checkout;
- install command;
- exact demo command;
- representative output with hashes abbreviated as examples rather than promised constants;
- walkthrough mapping each output line to `INTENT -> AUTHORITY -> MATERIALIZATION -> READBACK -> RECEIPT -> VERIFICATION`;
- explanation of the drift rejection and why no target mutation occurs;
- next links to `README.md`, `CLAIMS.md`, and `docs/AGENT_SECURITY_THREAT_MODEL.md`;
- explicit non-goals and production-claim boundary.

### `docs/YOUTUBE_AGENT_RELIABILITY_QUICKSTART_SCRIPT.md`
A concise recording script for the existing `RUMBO IA / @RumboAGI` channel.

The script must be derived from the exact public quickstart and include:
- opening problem statement;
- terminal commands shown on screen;
- PASS walkthrough;
- intentional state-drift demonstration;
- explanation of readback and receipt verification;
- closing claim boundary: reference implementation, not production certification or OpenAI affiliation.

Publishing a video is outside this repository change. The artifact is only a verified script ready for later recording.

### `README.md`
Add a compact `Start here: 5-minute reliability demo` section near the initial explanation, linking to `docs/QUICKSTART.md` and showing the single execution command. Do not duplicate the full tutorial in the README.

### `.github/workflows/test.yml`
Keep the existing Python 3.11/3.12/3.13 matrix and installed-import check. Add one matrix step after source installation:

```bash
python examples/reliable_tool_workflow.py
```

This turns the quickstart itself into CI-covered public behavior on every supported Python version.

## Error handling and output contract

The demo must distinguish expected safety rejection from unexpected failure:

- verified transition: print `PASS` only after `verify_transition` returns successfully;
- expected drift: catch only `ControlPlaneError`, require the exact reason `state drift after decision`, and print `FAIL-CLOSED`;
- any other exception or unexpected acceptance: print an error to stderr and return non-zero;
- never print secrets, environment variables, credentials, machine paths, or provider identifiers.

Output is for humans, not a stable machine protocol. Tests should assert semantic markers and state facts, not full receipt hashes or whitespace-perfect snapshots.

## Testing strategy

Implementation follows test-first order:
1. add failing example-contract tests;
2. implement the smallest example API needed to satisfy them without changing core behavior;
3. add/adjust QUICKSTART documentation;
4. add the CI execution step;
5. run the complete suite locally;
6. run the example directly from a clean installed checkout;
7. run `git diff --check` and a secret-like string scan on the diff;
8. push the candidate branch and require the public Python matrix to pass on its exact head SHA before merge.

## Acceptance gates

A candidate may be called `DEVEX QUICKSTART CANDIDATE` only when all of the following are true on the same branch head:

- existing legacy/control-plane/security tests pass;
- new quickstart contract tests pass;
- `python examples/reliable_tool_workflow.py` exits `0` and visibly reports both PASS and FAIL-CLOSED paths;
- installed package import checks remain green;
- Python 3.11/3.12/3.13 GitHub Actions matrix passes on the exact candidate SHA;
- `git diff --check` passes;
- no credential-like or private client data is present in the diff;
- README, QUICKSTART, example output, tests, and video script agree on the same behavior and claim boundaries.

Merge is a separate gate from branch CI. Public documentation must not say the quickstart is merged or released until that effect is read back from `main`.

## Claim boundaries

Allowed claims after exact-SHA branch CI passes:
- public reference implementation;
- executable quickstart;
- deterministic fail-closed state-drift demonstration;
- tested on the Python versions actually passing in the public matrix.

Disallowed claims without separate evidence:
- production deployment or enterprise scale;
- complete agent-security coverage;
- penetration testing or certification;
- OpenAI employment, endorsement, acceptance, or affiliation;
- customer usage, adoption, benchmark superiority, or reliability percentages.

## Rollback and isolation

The slice is additive except for small README/workflow edits. If the demo or documentation causes regressions, revert the quickstart commit(s) without altering `core.py` or `security.py`. No migration or persistent state exists.

## Planned implementation surface

Expected changed/added files only:
- `examples/reliable_tool_workflow.py`
- `tests/test_reliable_tool_workflow.py`
- `docs/QUICKSTART.md`
- `docs/YOUTUBE_AGENT_RELIABILITY_QUICKSTART_SCRIPT.md`
- `README.md`
- `.github/workflows/test.yml`

`src/verifiable_agent_control_plane/core.py`, `security.py`, and `__init__.py` are explicitly out of scope unless a failing test proves the approved public API cannot support the design; such a discovery upgrades scope and requires a design amendment before code changes.
