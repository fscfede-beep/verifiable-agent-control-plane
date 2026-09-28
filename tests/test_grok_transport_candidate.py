import unittest
from dataclasses import replace

from verifiable_agent_control_plane import (
    GrokTransportEnvelope,
    GrokTransportState,
    HumanKillSwitch,
    TransportCandidate,
    TransportCandidateError,
)


class GrokTransportCandidateContractTests(unittest.TestCase):
    def setUp(self):
        self.candidate = TransportCandidate(node_id="GROK_BUILD_PRIMARY")
        self.state = GrokTransportState()
        self.kill_switch = HumanKillSwitch(enabled=True)
        self.envelope = GrokTransportEnvelope(
            schema="rumbo-grok-transport-envelope-v1",
            message_id="msg-001",
            idempotency_key="idem-001",
            nonce="nonce-001",
            from_node="GROK_BUILD_PRIMARY",
            to_node="OPENAI_CHATGPT_PRIMARY",
            kind="evidence_handoff",
            payload={"artifact_sha256": "a" * 64},
        )

    def test_candidate_identity_is_explicit_and_never_authority_or_production(self):
        self.assertEqual(self.candidate.status, "CANDIDATE")
        self.assertFalse(self.candidate.is_authority)
        self.assertFalse(self.candidate.is_production)
        self.assertEqual(self.candidate.node_id, "GROK_BUILD_PRIMARY")

    def test_valid_envelope_is_accepted_with_hash_bound_receipt(self):
        next_state, receipt = self.candidate.accept(
            envelope=self.envelope,
            state=self.state,
            kill_switch=self.kill_switch,
        )
        self.assertEqual(next_state.sequence, 1)
        self.assertEqual(next_state.seen_nonces, ("nonce-001",))
        self.assertEqual(next_state.idempotency_keys, ("idem-001",))
        self.assertTrue(receipt.verify())
        self.assertEqual(receipt.status, "ACCEPTED")
        self.assertEqual(next_state.previous_receipt_hash, receipt.receipt_hash)

    def test_replay_nonce_fails_closed(self):
        next_state, _ = self.candidate.accept(
            envelope=self.envelope,
            state=self.state,
            kill_switch=self.kill_switch,
        )
        replay = replace(
            self.envelope,
            message_id="msg-002",
            idempotency_key="idem-002",
        )
        with self.assertRaisesRegex(TransportCandidateError, "replay nonce"):
            self.candidate.accept(
                envelope=replay,
                state=next_state,
                kill_switch=self.kill_switch,
            )

    def test_duplicate_idempotency_key_returns_same_receipt_without_advancing(self):
        next_state, receipt = self.candidate.accept(
            envelope=self.envelope,
            state=self.state,
            kill_switch=self.kill_switch,
        )
        duplicate = replace(
            self.envelope,
            message_id="msg-duplicate",
            nonce="nonce-duplicate",
        )
        duplicate_state, duplicate_receipt = self.candidate.accept(
            envelope=duplicate,
            state=next_state,
            kill_switch=self.kill_switch,
        )
        self.assertEqual(duplicate_state, next_state)
        self.assertEqual(duplicate_receipt, receipt)

    def test_schema_mismatch_fails_closed(self):
        bad = replace(self.envelope, schema="rumbo-grok-transport-envelope-v2")
        with self.assertRaisesRegex(TransportCandidateError, "schema mismatch"):
            self.candidate.accept(
                envelope=bad,
                state=self.state,
                kill_switch=self.kill_switch,
            )

    def test_unknown_kind_fails_closed(self):
        bad = replace(self.envelope, kind="execute_production")
        with self.assertRaisesRegex(TransportCandidateError, "kind not allowlisted"):
            self.candidate.accept(
                envelope=bad,
                state=self.state,
                kill_switch=self.kill_switch,
            )

    def test_human_kill_switch_blocks_before_state_change(self):
        disabled = HumanKillSwitch(enabled=False)
        with self.assertRaisesRegex(TransportCandidateError, "kill switch"):
            self.candidate.accept(
                envelope=self.envelope,
                state=self.state,
                kill_switch=disabled,
            )
        self.assertEqual(self.state, GrokTransportState())

    def test_wrong_target_node_fails_closed(self):
        bad = replace(self.envelope, to_node="PRODUCTION_CONTROL_PLANE")
        with self.assertRaisesRegex(TransportCandidateError, "target node"):
            self.candidate.accept(
                envelope=bad,
                state=self.state,
                kill_switch=self.kill_switch,
            )

    def test_receipt_tamper_is_detected(self):
        _, receipt = self.candidate.accept(
            envelope=self.envelope,
            state=self.state,
            kill_switch=self.kill_switch,
        )
        self.assertFalse(replace(receipt, sequence=99).verify())


if __name__ == "__main__":
    unittest.main()
