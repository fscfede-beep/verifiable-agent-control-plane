import unittest

from verifiable_agent_control_plane import (
    CanonicalProblemError,
    CanonicalProblemState,
    Evidence,
    advance,
    resume_state,
)


class CanonicalContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = Evidence(
            source="github",
            kind="commit",
            locator="example/repo@abc123",
            observed_at="2026-09-08T07:00:00Z",
            digest="sha256:" + "a" * 64,
        )
        self.state = CanonicalProblemState(
            problem_id="problem-001",
            title="Cross-chat continuity",
            objective="Resume the same problem safely in a new chat",
            status="EVIDENCE",
            evidence=(self.evidence,),
        )

    def test_state_digest_is_stable_and_sha256_bound(self) -> None:
        self.assertEqual(self.state.digest, self.state.digest)
        self.assertTrue(self.state.digest.startswith("sha256:"))
        self.assertEqual(len(self.state.digest), 71)

    def test_verified_state_requires_verified_evidence(self) -> None:
        stale = Evidence(
            source=self.evidence.source,
            kind=self.evidence.kind,
            locator=self.evidence.locator,
            observed_at=self.evidence.observed_at,
            digest=self.evidence.digest,
            status="stale",
        )
        with self.assertRaisesRegex(
            CanonicalProblemError, "VERIFIED state requires every evidence item"
        ):
            advance(self.state, status="VERIFIED", evidence=(stale,))


    def test_round_trip_json_preserves_canonical_state_and_digest(self) -> None:
        payload = self.state.to_json()
        restored = CanonicalProblemState.from_json(payload)
        self.assertEqual(restored.to_dict(), self.state.to_dict())
        self.assertEqual(restored.digest, self.state.digest)
        resumed = resume_state(restored)
        self.assertEqual(resumed["state_digest"], self.state.digest)

    def test_round_trip_rejects_unknown_schema(self) -> None:
        data = self.state.to_dict()
        data["schema_version"] = "999.0"
        with self.assertRaisesRegex(
            CanonicalProblemError, "unsupported canonical schema version"
        ):
            CanonicalProblemState.from_dict(data)

    def test_round_trip_rejects_malformed_json(self) -> None:
        with self.assertRaisesRegex(
            CanonicalProblemError, "invalid canonical JSON"
        ):
            CanonicalProblemState.from_json("{not-json}")

    def test_secret_like_material_fails_closed(self) -> None:
        state = CanonicalProblemState(
            problem_id="problem-002",
            title="Unsafe",
            objective="Reject secrets",
            status="DISCOVERY",
            verification={"api_key": "redacted"},
        )
        with self.assertRaisesRegex(
            CanonicalProblemError, "contains secret-like material"
        ):
            state.validate()

    def test_advance_increments_exactly_one_revision(self) -> None:
        next_state = advance(
            self.state,
            status="SOLVING",
            decisions=("Use durable canonical state",),
            next_actions=("Implement verifier",),
        )
        self.assertEqual(next_state.revision, self.state.revision + 1)
        self.assertEqual(next_state.problem_id, self.state.problem_id)

    def test_resume_contains_only_actionable_state(self) -> None:
        next_state = advance(
            self.state,
            status="VERIFYING",
            next_actions=("Run A/B verification",),
        )
        resumed = resume_state(next_state)
        self.assertEqual(resumed["problem_id"], "problem-001")
        self.assertEqual(resumed["revision"], 1)
        self.assertEqual(resumed["verified_evidence"], [self.evidence.locator])
        self.assertEqual(resumed["next_actions"], ["Run A/B verification"])
        self.assertEqual(resumed["state_digest"], next_state.digest)


if __name__ == "__main__":
    unittest.main()
