import unittest

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


class ExecutionIntegrityCodexR6Tests(unittest.TestCase):
    def test_composite_identity_and_replay_conflict(self):
        registry = TerminalRegistry()
        first = registry.terminalize(
            session_id="s1", turn_id="t1", tool_use_id="c",
            execution_state=ExecutionState.FINISHED,
            outcome=Outcome.COMPLETED,
            managed_writers_alive=False,
        )
        self.assertEqual(
            registry.terminalize(
                session_id="s1", turn_id="t1", tool_use_id="c",
                execution_state=ExecutionState.FINISHED,
                outcome=Outcome.COMPLETED,
                managed_writers_alive=False,
            ),
            first,
        )
        with self.assertRaisesRegex(ValueError, "terminal fact conflict"):
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
        self.assertNotEqual(second, first)

    def test_verified_effect_requires_quiescence_and_strict_snapshot_comparison(self):
        expected = {"approved": True, "meta": {"count": 1}}
        observed = {"approved": True, "meta": {"count": 1}}
        snapshot = EffectObservation(expected=expected, observed=observed)
        observed["meta"]["count"] = 2
        self.assertIs(snapshot.verdict(), EffectVerdict.VERIFIED)
        self.assertIs(
            EffectObservation(expected={"approved": True}, observed={"approved": 1}).verdict(),
            EffectVerdict.MISMATCH,
        )
        with self.assertRaisesRegex(ValueError, "verified effect requires quiescence"):
            TerminalRegistry().terminalize(
                session_id="s", turn_id="t", tool_use_id="c",
                execution_state=ExecutionState.FINISHED,
                outcome=Outcome.COMPLETED,
                managed_writers_alive=True,
                effect_verdict=EffectVerdict.VERIFIED,
            )

    def test_codex_pre_handler_outcomes_do_not_claim_execution(self):
        registry = TerminalRegistry()
        receipts = (
            terminalize_codex_finish(
                registry, session_id="s",
                finish=CodexFinish(turn_id="t1", call_id="c1", kind=CodexOutcomeKind.BLOCKED),
            ),
            terminalize_codex_finish(
                registry, session_id="s",
                finish=CodexFinish(
                    turn_id="t2", call_id="c2", kind=CodexOutcomeKind.FAILED,
                    handler_executed=False,
                ),
            ),
            terminalize_codex_finish(
                registry, session_id="s",
                finish=CodexFinish(
                    turn_id="t3", call_id="c3", kind=CodexOutcomeKind.ABORTED,
                    start_observed=False,
                ),
            ),
        )
        self.assertEqual(tuple(r.executed for r in receipts), (False, False, False))
        self.assertTrue(all(r.quiescence is Quiescence.QUIESCENT for r in receipts))

    def test_codex_finish_without_writer_evidence_stays_unknown(self):
        receipt = terminalize_codex_finish(
            TerminalRegistry(), session_id="s", finish=completed()
        )
        self.assertTrue(receipt.executed)
        self.assertIs(receipt.quiescence, Quiescence.UNKNOWN)

    def test_unified_exec_waits_for_correlated_exec_end(self):
        correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
        self.assertIsNone(correlator.observe_finish(completed()))
        self.assertEqual(len(correlator.registry), 0)
        receipt = correlator.observe_exec_end(
            CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
        )
        self.assertIsNotNone(receipt)
        self.assertIs(receipt.quiescence, Quiescence.QUIESCENT)

    def test_unified_exec_out_of_order_correlation_is_supported(self):
        correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
        self.assertIsNone(correlator.observe_exec_end(
            CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
        ))
        receipt = correlator.observe_finish(completed())
        self.assertIsNotNone(receipt)
        self.assertIs(receipt.quiescence, Quiescence.QUIESCENT)

    def test_unified_exec_unknown_exit_code_does_not_claim_quiescence(self):
        correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
        correlator.observe_finish(completed())
        receipt = correlator.observe_exec_end(
            CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=-1)
        )
        self.assertIsNotNone(receipt)
        self.assertIs(receipt.quiescence, Quiescence.UNKNOWN)

    def test_unmatched_turn_does_not_promote_other_call(self):
        correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
        correlator.observe_finish(completed(turn_id="t1"))
        self.assertIsNone(correlator.observe_exec_end(
            CodexExecEnd(turn_id="t2", call_id="c", process_id="42", exit_code=0)
        ))
        self.assertEqual(len(correlator.registry), 0)

    def test_conflicting_exec_end_is_rejected_and_replay_is_idempotent(self):
        correlator = CodexUnifiedExecCorrelator(TerminalRegistry(), session_id="s")
        event = CodexExecEnd(turn_id="t", call_id="c", process_id="42", exit_code=0)
        self.assertIsNone(correlator.observe_exec_end(event))
        self.assertIsNone(correlator.observe_exec_end(event))
        with self.assertRaisesRegex(ValueError, "ExecCommandEnd conflict"):
            correlator.observe_exec_end(
                CodexExecEnd(turn_id="t", call_id="c", process_id="43", exit_code=0)
            )

    def test_source_pin_is_explicit(self):
        self.assertEqual(CODEX_SOURCE_SHA, "60e35765c3e43e152bf5b382a38a0628efd70842")


if __name__ == "__main__":
    unittest.main()
