# Codex Execution Integrity r6

Status: `LOCAL_PASS`, runtime trace `NOT_EXECUTED`.

This integration brings the RUMBO Execution Integrity contract into the repository as native Python modules and regression tests. It is source-pinned to `openai/codex@ea3c4848d8481aa741475a7e29304115c1adb8aa` (observed 2026-09-14).

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

The correlator keys `ToolFinish` and `ExecCommandEnd` by `(turn_id, call_id)`. Source inspection of the pinned Codex commit shows the unified-exec watcher waits for process termination signalling and output drain before emitting `ExecCommandEnd`. However, the termination path can cancel the same token before an exit code is confirmed; Codex uses `-1` when no exit code is available.

Therefore this implementation promotes a pending receipt to `HOST_MANAGED/QUIESCENT` only when a correlated `ExecCommandEnd` has `exit_code != -1`. If `exit_code == -1`, quiescence remains `UNKNOWN`.

This claim is intentionally limited to the host-managed unified-exec process at the pinned source revision. It does not prove quiescence for MCP tools, arbitrary descendants, or external side effects.

## Verification state

- adapted package tests before publication: `39/39 PASS`
- reduced repository integration suite before publication: `10/10 PASS`
- Python compile check: `PASS`
- repository CI: pending until this branch/PR is evaluated
- real Codex runtime event ordering: `NOT_PROVEN`
- upstream Codex modification: `NOT_EXECUTED`
- production: `NO_GO`
