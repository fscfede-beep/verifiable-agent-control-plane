# RUMBO Agent Reliability Quickstart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a public, executable 5–10 minute reliability quickstart showing one verified transition and one deterministic fail-closed state-drift rejection.

**Architecture:** Keep the existing public package API unchanged. Add a standalone example that composes the public control-plane primitives, test the example as a developer-facing contract, then wire the exact command into documentation and the existing Python 3.11/3.12/3.13 CI matrix.

**Tech Stack:** Python 3.11+, stdlib `unittest`, existing zero-runtime-dependency package, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-devex-quickstart-design.md`

## Global Constraints

- No external API, LLM, MCP server, browser automation, database, network call, credential, or new runtime dependency.
- Do not change `core.py`, `security.py`, or `__init__.py` unless a failing test proves the approved public API is insufficient; stop for a design amendment if that occurs.
- Output must expose semantic PASS / FAIL-CLOSED evidence without secrets, machine paths, provider IDs, or stable-hash promises.
- Production, certification, customer-usage, benchmark-superiority, and OpenAI affiliation claims remain prohibited.
- Existing Python 3.11/3.12/3.13 matrix and installed-package import checks must remain intact.

---

### Task 1: Executable quickstart contract

**Files:**
- Create: `tests/test_reliable_tool_workflow.py`
- Create: `examples/reliable_tool_workflow.py`

**Interfaces:**
- Consumes: public imports from `verifiable_agent_control_plane`.
- Produces: `run_verified_transition() -> tuple[CanonicalState, Receipt, EffectResult]`, `run_state_drift_rejection() -> tuple[str, dict[str, object]]`, and `main() -> int`.
- [ ] **Step 1: Write failing contract tests**

Create `tests/test_reliable_tool_workflow.py` with `unittest`. Load `examples/reliable_tool_workflow.py` through `importlib.util.spec_from_file_location` so the tests exercise the real script file. Assert: verified transition reaches revision 1/checkpoint R1 and `verify_transition` has already succeeded; drift helper returns exact reason `state drift after decision` plus `{}` for blocked target state; `main()` returns 0 and stdout contains `PASS` and `FAIL-CLOSED`.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests.test_reliable_tool_workflow -v`
Expected: FAIL/ERROR because `examples/reliable_tool_workflow.py` does not exist.

- [ ] **Step 3: Implement minimal example**

Use public imports only. `run_verified_transition()` creates `CanonicalState`, `Policy({"set_value"})`, an `Intent`, calls `decide`, `materialize`, then `verify_transition`, and returns `(next_state, receipt, effect)`. `run_state_drift_rejection()` creates a stale accepted decision, advances a separate canonical state with a different intent, attempts stale materialization against the advanced state, requires `ControlPlaneError("state drift after decision")`, verifies a fresh blocked target still has `{}`, and returns `(reason, blocked_target.values.copy())`. `main()` prints human-readable PASS/FAIL-CLOSED evidence and returns non-zero on any unexpected outcome.

- [ ] **Step 4: Run GREEN and full regression suite**

Run: `python -m unittest tests.test_reliable_tool_workflow -v`
Expected: new tests PASS.
Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit Task 1**

`git add examples/reliable_tool_workflow.py tests/test_reliable_tool_workflow.py && git commit -m "feat: add reliability quickstart demo"`

### Task 2: Developer-facing tutorial and recording script

**Files:**
- Create: `docs/QUICKSTART.md`
- Create: `docs/YOUTUBE_AGENT_RELIABILITY_QUICKSTART_SCRIPT.md`

**Interfaces:**
- Consumes: exact command `python examples/reliable_tool_workflow.py` and semantic markers from Task 1.
- Produces: first-run tutorial and an evidence-aligned recording script; neither changes runtime behavior.
- [ ] **Step 1: Write QUICKSTART from observed behavior**

Document prerequisites, `python -m pip install .`, the exact demo command, representative semantic output, the mapping `INTENT -> AUTHORITY -> MATERIALIZATION -> READBACK -> RECEIPT -> VERIFICATION`, why state drift is rejected before target mutation, and links to README/CLAIMS/threat model. Receipt hashes in sample output must be abbreviated placeholders such as `<sha256...>`, never asserted constants.

- [ ] **Step 2: Write YouTube script from the same contract**

Create a short recording script for `RUMBO IA / @RumboAGI` that shows the same install/demo commands, explains the PASS path and intentional drift rejection, and closes with the exact boundary: public reference implementation; not production certification and no OpenAI affiliation.

- [ ] **Step 3: Verify docs agree with executable markers**

Run a Python one-liner that reads both docs and asserts presence of `python examples/reliable_tool_workflow.py`, `PASS`, `FAIL-CLOSED`, `state drift`, and the claim-boundary phrases. Run the demo once and compare terminology manually against docs.

- [ ] **Step 4: Commit Task 2**

`git add docs/QUICKSTART.md docs/YOUTUBE_AGENT_RELIABILITY_QUICKSTART_SCRIPT.md && git commit -m "docs: add reliability quickstart guide"`

### Task 3: README and CI integration

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/test.yml`

**Interfaces:**
- Consumes: quickstart command and docs from Tasks 1–2.
- Produces: visible entry point plus CI execution on every supported Python version.

- [ ] **Step 1: Add README start-here block**

Near the initial explanation add `## Start here: 5-minute reliability demo`, link `docs/QUICKSTART.md`, and show only `python examples/reliable_tool_workflow.py` after source install. Keep the full walkthrough in QUICKSTART.

- [ ] **Step 2: Add CI demo execution step**

After `Install package from source`, add:
```yaml
      - name: Run reliability quickstart
        run: python examples/reliable_tool_workflow.py
```
Keep all existing matrix versions and installed-import verification unchanged.

- [ ] **Step 3: Verify local behavior and workflow diff**

Run full unittest suite, direct demo, `git diff --check`, and inspect `.github/workflows/test.yml` to ensure only the one additive step changed.

- [ ] **Step 4: Commit Task 3**

`git add README.md .github/workflows/test.yml && git commit -m "ci: verify reliability quickstart"`

### Task 4: Candidate verification, privacy audit, and PR

**Files:** all changed files from Tasks 1–3 plus this plan/spec for review only.

- [ ] **Step 1: Run full fresh verification**

Run `python -m unittest discover -s tests -v`, `python examples/reliable_tool_workflow.py`, and `git diff --check` from the candidate branch. All must exit 0.

- [ ] **Step 2: Run privacy/claim scan**

Search the candidate diff for credential markers (`api_key`, `password`, `authorization`, `private_key`), private machine paths, client identifiers, and prohibited claims (`production deployment`, `OpenAI endorsement`, `OpenAI affiliation`). Any real finding blocks promotion until removed; test fixtures/docs that explicitly describe rejected secret keys must be reviewed contextually rather than blindly treated as leaks.

- [ ] **Step 3: Push candidate and create PR**

Push exact head SHA, create a PR to `main` summarizing behavior, tests, claim boundaries, and that merge is not yet production/release evidence.

- [ ] **Step 4: Verify exact-SHA CI**

Read GitHub Actions for the PR head. Require all Python 3.11/3.12/3.13 jobs PASS on the exact candidate SHA before calling it `DEVEX QUICKSTART CANDIDATE`.

- [ ] **Step 5: Final review**

Compare changed paths against the spec allowlist, re-read README/QUICKSTART/video script for consistency, and report actual branch/PR/CI state. Do not merge without a separate finish-branch decision.
