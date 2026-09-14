# Codex runtime trace gate

This document defines the evidence format consumed by `verify_runtime_trace`.
It is intentionally narrower than a general Codex event log.

Source contract pin:

`openai/codex@60e35765c3e43e152bf5b382a38a0628efd70842`

Revalidated on 2026-09-14 against the then-current `main`. `ToolFinishInput` still exposes `Completed`, `Blocked`, `Failed { handler_executed }`, and `Aborted`; unified-exec still emits `ExecCommandEnd` only after its cancellation/exit signal path and output drain, while failure/unknown termination can surface `exit_code == -1`. Therefore `exit_code != -1` remains the required condition for this verifier to promote host-managed quiescence.

## Accepted JSONL event shapes

A captured trace may be normalized to one JSON object per line.

Completed tool finish:

```json
{"type":"ToolFinish","turn_id":"turn-1","call_id":"call-1","kind":"completed","completed_success":true}
```

Failed tool finish:

```json
{"type":"ToolFinish","turn_id":"turn-1","call_id":"call-1","kind":"failed","handler_executed":true}
```

Aborted tool finish:

```json
{"type":"ToolFinish","turn_id":"turn-1","call_id":"call-1","kind":"aborted","start_observed":true}
```

Blocked pre-handler finish:

```json
{"type":"ToolFinish","turn_id":"turn-1","call_id":"call-1","kind":"blocked"}
```

Unified-exec terminal event:

```json
{"type":"ExecCommandEnd","turn_id":"turn-1","call_id":"call-1","process_id":"4242","exit_code":0}
```

## Verification command

After `pip install .`:

```bash
codex-trace-verify trace.jsonl --session-id SESSION_ID
```

Direct module invocation remains equivalent:

```bash
python -m verifiable_agent_control_plane.codex_trace_cli trace.jsonl --session-id SESSION_ID
```

The command prints one machine-readable JSON object. Exit status is deliberately fail-closed:

- `0`: `PASS`
- `2`: `UNKNOWN`
- `3`: `MISMATCH`

The output includes the pinned Codex source SHA, event/finish/receipt counts, unresolved `(turn_id, call_id)` keys, errors, and the SHA-256 of each terminal receipt.

## Verdicts

- `PASS`: every observed `ToolFinish` has a verified terminal receipt and host-managed quiescence is proven.
- `UNKNOWN`: evidence is incomplete, including a missing required `ExecCommandEnd`, unmatched terminal event, or `exit_code == -1`.
- `MISMATCH`: input is malformed or material facts conflict for the same `(turn_id, call_id)`.

Non-object JSONL entries are malformed evidence and therefore `MISMATCH`, not an uncaught parser condition.

## Claim boundary

`PASS` only establishes the contract represented by the normalized events for the pinned Codex source revision. It does not prove OpenAI upstream acceptance, MCP quiescence, unmanaged-descendant quiescence, or production readiness.

The remaining real-runtime evidence gate is tracked in #54.
