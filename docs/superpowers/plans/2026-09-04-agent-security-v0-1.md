# Agent Security V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic principal/delegation/provenance security gates and identity-bound receipts to the existing Verifiable Agent Control Plane without changing legacy core semantics.

**Architecture:** A new `security.py` composes over the existing core rather than modifying it. Pure evaluation binds identity, delegation, resource scope, provenance, policy and approval; secure materialization re-evaluates immediately before the existing core materialization; verification binds the core receipt to the security context.

**Tech Stack:** Python 3.11+, stdlib `dataclasses`, `hashlib`, `json`, `unittest`; zero runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-09-04-agent-security-v0-1-design.md`

## Global Constraints

- Keep runtime dependency count at zero.
- No external network calls or credential reads in production code.
- Preserve all 16 existing tests and public API compatibility.
- Do not modify `core.py` unless a failing test proves it is necessary.
- All tests use synthetic/in-memory targets.
- Production and certification claims remain `NO_GO`.

---

### Task 1: Principal, delegation, grants and resource isolation

**Files:**
- Create: `tests/test_agent_security.py`
- Create: `src/verifiable_agent_control_plane/security.py`

**Interfaces:**
- Produces: `Principal`, `Delegation`, `ActionGrant`, `SecurityPolicy`, `SecurityDecision`, `evaluate_security`.

- [ ] **Step 1: Write RED tests S01 and S02**

Create principals `user-a` and `service-agent`, a grant/delegation scoped to `record:a`, and assert that `evaluate_security(... requested_resources=frozenset({'record:b'}))` returns `accepted=False` and reason `resource outside principal scope`. Add the matching `record:a` case and expect acceptance only after implementation.

- [ ] **Step 2: Verify RED**

Run: `.venv\\Scripts\\python.exe -m unittest tests.test_agent_security -v`

Expected before production code: import failure because `verifiable_agent_control_plane.security` does not exist.

- [ ] **Step 3: Implement minimal immutable models and evaluator**

Implement frozen dataclasses with deterministic SHA-256 digest properties. `evaluate_security` checks policy grant first, exact delegation requester/executor binding, active/expiry, allowed action, and resource scope. It returns a frozen `SecurityDecision` and never mutates state.

- [ ] **Step 4: Verify GREEN + regression**

Run the focused security tests, then `python -m unittest discover -s tests -v`. Expected: all tests PASS.

- [ ] **Step 5: Commit**

`git add src/verifiable_agent_control_plane/security.py tests/test_agent_security.py && git commit -m "feat: bind agent actions to principal delegation"`

---

### Task 2: Provenance and untrusted-context isolation

**Files:**
- Modify: `src/verifiable_agent_control_plane/security.py`
- Modify: `tests/test_agent_security.py`

**Interfaces:**
- Produces: `ContextArtifact`; `SecurityDecision.provenance_digest`.

- [ ] **Step 1: Write RED tests S03, S04 and S07**

Add untrusted `ContextArtifact` instances for tool metadata, a shared agent channel and telemetry. Assert that context does not create a grant: privileged or non-granted actions remain rejected. Add a granted action case and assert the returned decision contains deterministic provenance bound to the supplied artifacts.

- [ ] **Step 2: Verify RED**

Run focused tests. Expected: failure because `ContextArtifact` / provenance binding is missing.

- [ ] **Step 3: Implement minimal provenance binding**

Hash an artifact list in deterministic artifact-id/digest order. Context participates in decision evidence only; it is never consulted as an authorization source.

- [ ] **Step 4: Verify GREEN + regression**

Run focused tests and complete suite; all PASS.

- [ ] **Step 5: Commit**

`git add src/verifiable_agent_control_plane/security.py tests/test_agent_security.py && git commit -m "feat: bind untrusted context provenance"`

---

### Task 3: Approval, drift-safe materialization and security receipts

**Files:**
- Modify: `src/verifiable_agent_control_plane/security.py`
- Modify: `tests/test_agent_security.py`

**Interfaces:**
- Produces: `ApprovalEvidence`, `SecurityReceipt`, `secure_materialize`, `verify_security_transition`.

- [ ] **Step 1: Write RED tests S05, S06, S08, S09 and S10**

Tests must prove: changed/inactive delegation is rejected before execution; an effect action mismatch still fails through the core; required approval without `verification_digest` is rejected; changed artifact digest after decision is rejected; a security receipt generated for principal A cannot verify under principal B.

- [ ] **Step 2: Verify RED**

Run focused tests. Expected failures are missing approval/materialization/receipt interfaces, not syntax errors.

- [ ] **Step 3: Implement approval checks**

For approval-required actions, require exact intent digest, requester principal, action, `approved=True`, and non-empty `verification_digest`.

- [ ] **Step 4: Implement secure materialization**

Re-run `evaluate_security` with current inputs. If it is rejected or differs from the accepted prior `SecurityDecision`, raise `ControlPlaneError` before calling core `materialize`. On success, wrap the core receipt in a hash-bound `SecurityReceipt`.

- [ ] **Step 5: Implement security verification**

Call core `verify_transition`, verify the security receipt hash, then compare core receipt hash and all requester/executor/delegation/resource/provenance/policy/approval/evaluation digests. Reject mismatches fail-closed.

- [ ] **Step 6: Verify GREEN + regression**

Run focused tests and full suite. Expected: all PASS with no warnings/errors.

- [ ] **Step 7: Commit**

`git add src/verifiable_agent_control_plane/security.py tests/test_agent_security.py && git commit -m "feat: add drift-safe security receipts"`

---

### Task 4: Public API, threat-model documentation and exact-SHA verification

**Files:**
- Modify: `src/verifiable_agent_control_plane/__init__.py`
- Create: `docs/AGENT_SECURITY_THREAT_MODEL.md`
- Modify: `README.md`
- Do not modify `CLAIMS.md` until exact-SHA CI is successful.

**Interfaces:**
- Publicly export the V0.1 security types and functions from `verifiable_agent_control_plane`.

- [ ] **Step 1: Write RED package-surface test**

Extend `tests/test_package_surface.py` to assert the security public names exist from the installed package.

- [ ] **Step 2: Verify RED**

Reinstall from source into `.venv`, run package-surface test, and confirm missing exports fail.

- [ ] **Step 3: Export names and document the threat model**

Update `__init__.py`; add a concise defensive/synthetic threat-model document; update README with a bounded Agent Security section and explicit non-claims.

- [ ] **Step 4: Verify local candidate**

Reinstall from source; run all tests; run installed import from outside checkout. Expected: PASS.

- [ ] **Step 5: Commit**

`git add src/verifiable_agent_control_plane/__init__.py tests/test_package_surface.py docs/AGENT_SECURITY_THREAT_MODEL.md README.md && git commit -m "docs: expose agent security evaluation surface"`

- [ ] **Step 6: Push candidate branch and verify CI**

Push `agent-security-v0-1` without modifying `main`. Verify GitHub Actions Python 3.11/3.12/3.13 on the exact branch SHA. Only after success may the branch be reported as `V0.1 SECURITY CANDIDATE`; merge/release remain separate gates.
