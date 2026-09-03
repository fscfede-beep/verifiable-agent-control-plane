import unittest
from dataclasses import replace

from verifiable_agent_control_plane import (
    CanonicalState,
    ControlPlaneError,
    Decision,
    EffectResult,
    InMemoryTarget,
    Intent,
    Policy,
    decide,
    materialize,
    validate_intent,
    verify_transition,
)


class ControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = CanonicalState()
        self.policy = Policy(frozenset({"set_value"}))
        self.intent = Intent(
            intent_id="intent-001",
            expected_revision=0,
            expected_checkpoint="ZERO",
            action="set_value",
            payload={"key": "mode", "value": "safe"},
        )

    def test_01_exact_state_intent_is_accepted(self):
        decision = decide(self.intent, self.state, self.policy)
        self.assertTrue(decision.accepted)

    def test_02_stale_revision_is_rejected(self):
        intent = replace(self.intent, expected_revision=1)
        decision = decide(intent, self.state, self.policy)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "stale revision")

    def test_03_stale_checkpoint_is_rejected(self):
        intent = replace(self.intent, expected_checkpoint="R9")
        decision = decide(intent, self.state, self.policy)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "stale checkpoint")

    def test_04_duplicate_intent_is_rejected(self):
        state = replace(self.state, processed_intents=("intent-001",))
        with self.assertRaisesRegex(ControlPlaneError, "duplicate intent"):
            validate_intent(self.intent, state, self.policy)

    def test_05_non_allowlisted_action_is_rejected(self):
        intent = replace(self.intent, action="delete_everything")
        decision = decide(intent, self.state, self.policy)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "action not allowlisted")

    def test_06_secret_like_payload_is_rejected(self):
        intent = replace(self.intent, payload={"api_key": "do-not-publish"})
        decision = decide(intent, self.state, self.policy)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "secret-like payload rejected")

    def test_07_decision_phase_is_read_only(self):
        before = self.state
        decide(self.intent, self.state, self.policy)
        self.assertEqual(self.state, before)

    def test_08_materialize_advances_exactly_one_revision(self):
        target = InMemoryTarget()
        decision = decide(self.intent, self.state, self.policy)
        next_state, receipt, effect = materialize(
            intent=self.intent,
            decision=decision,
            state=self.state,
            policy=self.policy,
            execute=target.execute,
        )
        self.assertEqual(next_state.revision, 1)
        self.assertEqual(next_state.checkpoint, "R1")
        verify_transition(
            prior_state=self.state,
            next_state=next_state,
            intent=self.intent,
            receipt=receipt,
            effect=effect,
        )

    def test_09_state_drift_after_decision_fails_closed(self):
        decision = decide(self.intent, self.state, self.policy)
        drifted = replace(self.state, revision=1, checkpoint="R1")
        with self.assertRaisesRegex(ControlPlaneError, "state drift after decision"):
            materialize(
                intent=self.intent,
                decision=decision,
                state=drifted,
                policy=self.policy,
                execute=InMemoryTarget().execute,
            )

    def test_10_rejected_decision_cannot_materialize(self):
        decision = Decision(
            intent_id=self.intent.intent_id,
            intent_digest=self.intent.digest,
            state_digest=self.state.digest,
            accepted=False,
            reason="no",
        )
        with self.assertRaisesRegex(ControlPlaneError, "rejected decision"):
            materialize(
                intent=self.intent,
                decision=decision,
                state=self.state,
                policy=self.policy,
                execute=InMemoryTarget().execute,
            )

    def test_11_readback_mismatch_fails_closed(self):
        def bad_execute(action, payload):
            return EffectResult(
                effect_id="bad-effect",
                action=action,
                requested_payload=dict(payload),
                observed_payload={"key": "mode", "value": "unsafe"},
            )

        decision = decide(self.intent, self.state, self.policy)
        with self.assertRaisesRegex(ControlPlaneError, "readback mismatch"):
            materialize(
                intent=self.intent,
                decision=decision,
                state=self.state,
                policy=self.policy,
                execute=bad_execute,
            )

    def test_12_receipt_chain_is_bound_to_transition(self):
        target = InMemoryTarget()
        decision = decide(self.intent, self.state, self.policy)
        next_state, receipt, effect = materialize(
            intent=self.intent,
            decision=decision,
            state=self.state,
            policy=self.policy,
            execute=target.execute,
        )
        self.assertTrue(receipt.verify())
        self.assertEqual(next_state.previous_receipt_hash, receipt.receipt_hash)
        verify_transition(
            prior_state=self.state,
            next_state=next_state,
            intent=self.intent,
            receipt=receipt,
            effect=effect,
        )

    def test_13_tampered_receipt_is_rejected(self):
        target = InMemoryTarget()
        decision = decide(self.intent, self.state, self.policy)
        next_state, receipt, effect = materialize(
            intent=self.intent,
            decision=decision,
            state=self.state,
            policy=self.policy,
            execute=target.execute,
        )
        tampered = replace(receipt, to_revision=99)
        with self.assertRaisesRegex(ControlPlaneError, "receipt hash mismatch"):
            verify_transition(
                prior_state=self.state,
                next_state=next_state,
                intent=self.intent,
                receipt=tampered,
                effect=effect,
            )

    def test_14_processed_intent_cannot_be_applied_twice(self):
        target = InMemoryTarget()
        decision = decide(self.intent, self.state, self.policy)
        next_state, _, _ = materialize(
            intent=self.intent,
            decision=decision,
            state=self.state,
            policy=self.policy,
            execute=target.execute,
        )
        replay = replace(
            self.intent,
            expected_revision=next_state.revision,
            expected_checkpoint=next_state.checkpoint,
        )
        decision2 = decide(replay, next_state, self.policy)
        self.assertFalse(decision2.accepted)
        self.assertEqual(decision2.reason, "duplicate intent")


if __name__ == "__main__":
    unittest.main()
