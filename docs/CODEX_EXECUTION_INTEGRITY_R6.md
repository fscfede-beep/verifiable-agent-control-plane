# Codex Execution Integrity r6

Status: `LOCAL_PASS`, runtime trace `NOT_EXECUTED`.

This integration brings the RUMBO Execution Integrity contract into the repository as native Python modules and regression tests. It is source-pinned to `openai/codex@60e35765c3e43e152bf5b382a38a0628efd70842` (revalidated 2026-09-14 against the then-current `main`).

## Contract

A tool call is represented as separate facts:

- execution state: `NOT_STARTED | STARTED | FINISHED`
- outcome: `BLOCKED | COMPLETED | FAILED | CANCELLED | UNKNOWN`
- quiescence: `QUIESCENT | NOT_QUIESCENT | UNKNOWN`
- effect verdict: `VERIFIED | MISMATCH | UNKNOWN`

The exactly-once receipt identity is `(session_id, turn_id, tool_use_id)`. Identical replay is idempotent; conflicting replay is rejected.

## Codex mapping

`ToolCallOutcome::Blocked` maps to `NOT_STARTED/BLOCKED`.

`ToolCallOutcome::Failed { handler_executed: false }` maps to `NOT_STARTED/FAILED`; with `handler_executed: true` it maps to `FINISHED/FAILED`.

`Aborted` can occur before dispatch accepts the call. The adapter therefore requires an explicit `start_observed` fact before deciding whether execution began.

## Unified-exec quiescence

The correlator keys `ToolFinish` and `ExecCommandEnd` by `(turn_id, call_id)`. Source inspection of the pinned Codex commit shows the unified-exec watcher waits for the cancellation/exit signalling path and output drain before emitting `ExecCommandEnd`. The termination/failure paths can still produce no confirmed exit code; Codex represents that terminal uncertainty with `exit_code == -1` in the relevant failure path.

Therefore this implementation promotes a pending receipt to `HOST_MANAGED/QUIESCENT` only when a correlated `ExecCommandEnd` has `exit_code != -1`. If `exit_code == -1`, quiescence remains `UNKNOWN`.

This claim is intentionally limited to the host-managed unified-exec process at the pinned source revision. It does not prove quiescence for MCP tools, arbitrary descendants, or external side effects.

## Verification state

- adapted package tests before publication: `39/39 PASS`
- reduced repository integration suite before publication: `10/10 PASS`
- runtime trace verifier suite: `10/10 PASS`
- CLI runner suite: `4/4 PASS`
- installed console script: covered by repository tests
- Python compile check: `PASS`
- prior repository CI on the preceding head: `PASS` on Python 3.11/3.12/3.13 + Twin Bridge A/B
- current source-pin update: requires fresh CI on the new head
- real Codex runtime event ordering: `NOT_PROVEN`
- upstream Codex modification: `NOT_EXECUTED`
- production: `NO_GO`
