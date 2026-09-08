import json
import unittest
from dataclasses import replace

from verifiable_agent_control_plane import (
    BRAND,
    BRAND_NAMESPACE,
    CanonicalProblemError,
    CanonicalProblemState,
    ContinuityEvent,
    ContinuityLedger,
    advance,
)


class ContinuityLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state0 = CanonicalProblemState(
            problem_id="ledger-problem",
            brand=BRAND,
            brand_record_id=f"{BRAND_NAMESPACE}/verifiable-agent-control-plane/ledger-problem/0",
            title="Ledger",
            objective="Keep continuity auditable",
            status="DISCOVERY",
        )
        self.state1 = advance(self.state0, status="EVIDENCE")
        self.state2 = advance(
            self.state1,
            status="VERIFYING",
            next_actions=("verify",),
        )

    def test_ledger_chain_and_state_binding(self) -> None:
        ledger = ContinuityLedger().append(self.state0, "discover").append(
            self.state1, "collect"
        ).append(self.state2, "verify")
        ledger.verify(self.state2)
        restored = ContinuityLedger.from_json(ledger.to_json())
        restored.verify(self.state2)

    def test_tampered_event_is_rejected(self) -> None:
        ledger = ContinuityLedger().append(self.state0, "discover").append(
            self.state1, "collect"
        )
        broken = replace(ledger.events[1], action="forged")
        bad = ContinuityLedger((ledger.events[0], broken))
        with self.assertRaisesRegex(CanonicalProblemError, "event hash mismatch"):
            bad.verify()

    def test_mixed_projects_fail_closed(self) -> None:
        ledger = ContinuityLedger().append(self.state0, "discover", project="alpha")
        event = ContinuityEvent.build(
            state=self.state1,
            action="collect",
            previous_event_hash=ledger.events[-1].event_hash,
            project="beta",
        )
        bad = ContinuityLedger(ledger.events + (event,))
        with self.assertRaisesRegex(CanonicalProblemError, "project mismatch"):
            bad.verify()

    def test_mixed_problem_ids_fail_closed(self) -> None:
        ledger = ContinuityLedger().append(self.state0, "discover")
        event = ContinuityEvent.build(
            state=self.state2,
            action="jump",
            previous_event_hash=ledger.events[-1].event_hash,
        )
        bad = ContinuityLedger(ledger.events + (event,))
        with self.assertRaisesRegex(CanonicalProblemError, "problem mismatch"):
            bad.verify()

    def test_revision_gap_is_rejected(self) -> None:
        ledger = ContinuityLedger().append(self.state0, "discover")
        event = ContinuityEvent(
            brand=BRAND,
            brand_record_id=f"{BRAND_NAMESPACE}/verifiable-agent-control-plane/ledger-problem/2",
            problem_id=self.state0.problem_id,
            revision=2,
            state_digest=self.state2.digest,
            action="jump",
            previous_event_hash=ledger.events[-1].event_hash,
            event_hash="0" * 64,
        )
        bad = ContinuityLedger(ledger.events + (event,))
        with self.assertRaisesRegex(CanonicalProblemError, "event hash mismatch"):
            bad.verify()

    def test_missing_event_field_fails_closed(self) -> None:
        data = json.loads(
            ContinuityLedger().append(self.state0, "discover").to_json()
        )
        del data["events"][0]["action"]
        with self.assertRaisesRegex(CanonicalProblemError, "missing required fields"):
            ContinuityLedger.from_json(json.dumps(data))

    def test_invalid_digest_is_rejected(self) -> None:
        event = ContinuityEvent(
            problem_id=self.state0.problem_id,
            revision=0,
            state_digest="z" * 64,
            action="discover",
            previous_event_hash=None,
            event_hash="0" * 64,
        )
        self.assertFalse(event.verify())

    def test_negative_revision_is_rejected(self) -> None:
        event = ContinuityEvent(
            brand=BRAND,
            brand_record_id=f"{BRAND_NAMESPACE}/verifiable-agent-control-plane/ledger-problem/-1",
            problem_id=self.state0.problem_id,
            revision=-1,
            state_digest=self.state0.digest,
            action="discover",
            previous_event_hash=None,
            event_hash="0" * 64,
        )
        self.assertFalse(event.verify())

    def test_empty_action_fails_closed(self) -> None:
        with self.assertRaisesRegex(CanonicalProblemError, "action must be non-empty"):
            ContinuityEvent.build(
                state=self.state0,
                action="",
                previous_event_hash=None,
            )


if __name__ == "__main__":
    unittest.main()
