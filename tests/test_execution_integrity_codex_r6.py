import pytest

from verifiable_agent_control_plane.codex_adapter import (
    CodexFinish,
    CodexOutcomeKind,
    terminalize_codex_finish,
)
from verifiable_agent_control_plane.codex_quiescence import (
    CODEX_SOURCE_SHA,
    CodexExecEnd,
    CodexUnifiedExecCorrelator,
)
from verifiable_agent_control_plane.execution_integrity import (
    EffectObservation,
    EffectVerdict,
    ExecutionState,
    Outcome,
    Quiescence,
    TerminalRegistry,
)


def completed(call_id="c", turn_id="t") -> CodexFinish:
    return CodexFinish(
        turn_id=turn_id,
        call_id=call_id,
        kind=CodexOutcomeKind.COMPLETED,
        completed_success=True,
    )


def test_composite_identity_and_replay_conflict():
    registry = TerminalRegistry()
    first = registry.terminalize(
        session_id="s1", turn_id="t1", tool_use_id="c",
        execution_state=ExecutionState.FINISHED,
        outcome=Outcome.COMPLETED,
        managed_writers_alive=False,
    )
    assert registry.terminalize(
        session_id="s1", turn_id="t1", tool_use_id="c",
        execution_state=ExecutionState.FINISHED,
        outcome=Outcome.COMPLETED,
        managed_writers_alive=False,
    ) == first
    with pytest.raises(ValueError, match="terminal fact conflict"):
        registry.terminalize(
            session_id="s1", turn_id="t1", tool_use_id="c",
            execution_state=ExecutionState.FINISHED,
            outcome=Outcome.FAILED,
            managed_writers_alive=False,
        )
    second = registry.terminalize(
        session_id="s2", turn_id="t1", tool_use_id="c",
        execution_state=ExecutionState.FINISHED,
        outcome=Outcome.COMPLETED,
        managed_writers_alive=False,
    )
    assert second != first


def test_verified_effect_requires_quiescence_and_strict_snapshot_comparison():
    expected = {"approved": True, "meta": {"count": 1}}
    observed = {"approved": True, "meta": {"count": 1}}
    snapshot = EffectObservation(expected=expected, observed=observed)
    observed["meta"]["count"] = 2
    assert snapshot.verdict() is EffectVerdict.VERIFIED
    assert EffectObservation(expected={"approved": True}, observed={"approved": 1}).verdict() is EffectVerdict.MISMATCH

    registry = TerminalRegistry()
    with pytest.raises(ValueError, match="verified effect requires quiescence"):
        registry.terminalize(
            session_id="s", turn_id="t", tool_use_id="c",
            execution_state=ExecutionState.FINISHED,
            outcome=Outcome.COMPLETED,
            managed_writers_alive=True,
            effect_verdict=EffectVerdict.VERIFIED,
        )


def test_codex_pre_handler_outcomes_do_not_claim_execution():
    registry = TerminalRegistry()
    blocked = terminalize_codex_finish(
        registry, session_id="s",
        finish=CodexFinish(turn_id="t1", call_id="c1", kind=CodexOutcomeKind.BLOCKED),
    )
    failed = terminalize_codex_finish(
        registry, session_id="s",
        finish=CodexFinish(
            turn_id="t2", call_id="c2", kind=CodexOutcomeKind.FAILED,
            handler_executed=False,
        ),
    )
    aborted = terminalize_codex_finish(
        registry, session_id="s",
        finish=CodexFinish(
            turn_id="t3", call_id="c3", kind=CodexOutcomeKind.ABORTED,
            start_observed=False,
        ),
    )
    assert (blocked.executed, failed.executed, aborted.executed) == (False, False, False)
    assert all(r.quiescence is Quiescence.QUIESCENT for r in (blocked, failed, aborted))


def test_codex_finish_without_writer_evidence_stays_unknown():
    receipt = terminalize_codex_finish(
        TerminalRegistry(), session_id="s", finish=completed()
    )
    assert receipt.executed is True
    assert receipt.quiescence is Quiescence.UNKNOWN


def test_unified_exec_waits_for_correlated_exec_end():
    correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
    assert correlator.observe_finish(completed()) is None
    assert len(correlator.registry) == 0
    receipt = correlator.observe_exec_end(
        CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
    )
    assert receipt is not None
    assert receipt.quiescence is Quiescence.QUIESCENT


def test_unified_exec_out_of_order_correlation_is_supported():
    correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
    assert correlator.observe_exec_end(
        CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
    ) is None
    receipt = correlator.observe_finish(completed())
    assert receipt is not None
    assert receipt.quiescence is Quiescence.QUIESCENT


def test_unified_exec_unknown_exit_code_does_not_claim_quiescence():
    correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
    correlator.observe_finish(completed())
    receipt = correlator.observe_exec_end(
        CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=-1)
    )
    assert receipt is not None
    assert receipt.quiescence is Quiescence.UNKNOWN


def test_unmatched_turn_does_not_promote_other_call():
    correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
    correlator.observe_finish(completed(turn_id="t1"))
    assert correlator.observe_exec_end(
        CodexExecEnd(turn_id="t2", call_id="c", process_id="42", exit_code=0)
    ) is None
    assert len(correlator.registry) == 0


def test_conflicting_exec_end_is_rejected_and_identical_replay_is_idempotent():
    correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
    event = CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
    assert correlator.observe_exec_end(event) is None
    assert correlator.observe_exec_end(event) is None
    with pytest.raises(ValueError, match="ExecCommandEnd conflict"):
        correlator.observe_exec_end(
            CodexExecEnd(turn_id="t", call_id="c", process_id="43", exit_code=0)
        )


def test_source_pin_is_explicit():
    assert CODEX_SOURCE_SHA == "ea3c4848d8481aa741475a7e29304115c1adb8aa"
