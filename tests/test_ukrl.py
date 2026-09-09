import unittest
from ukrl import Claim, UKRL, STATUS_ACTIVE, STATUS_CONFLICT, STATUS_STALE, STATUS_UNVERIFIED, assert_fail_closed

NOW = "2026-09-09T08:20:00Z"

class TestUKRL(unittest.TestCase):
    def setUp(self):
        self.r = UKRL(["github", "stele"])

    def test_verified_canonical_wins_over_secondary(self):
        report = self.r.reconcile([
            Claim("a", "software", "source", "github", "github", "2026-09-09T08:00:00Z", True, "canonical", "sha:a"),
            Claim("b", "software", "source", "memory", "memory", "2026-09-09T08:10:00Z", True, "verified", "mem:b"),
        ], NOW)
        self.assertEqual(report.resolutions[0].status, STATUS_ACTIVE)
        self.assertEqual(report.resolutions[0].selected.claim_id, "a")

    def test_two_verified_canonical_sources_conflict(self):
        report = self.r.reconcile([
            Claim("a", "twin", "status", "PASS", "github", "2026-09-09T08:00:00Z", True, "canonical", "sha:a"),
            Claim("b", "twin", "status", "PENDING", "stele", "2026-09-09T08:01:00Z", True, "canonical", "stele:b"),
        ], NOW)
        self.assertEqual(report.resolutions[0].status, STATUS_CONFLICT)
        with self.assertRaises(RuntimeError):
            assert_fail_closed(report)

    def test_unverified_claim_does_not_become_truth(self):
        report = self.r.reconcile([
            Claim("a", "account", "other_account_access", "true", "chat-history", "2026-09-09T08:00:00Z", False, "secondary", None),
        ], NOW)
        self.assertEqual(report.resolutions[0].status, STATUS_UNVERIFIED)

    def test_stale_claim_fails_closed(self):
        report = self.r.reconcile([
            Claim("a", "agent", "model", "gpt-6", "github", "2026-01-01T00:00:00Z", True, "canonical", "sha:a"),
        ], NOW, max_age_days=30)
        self.assertEqual(report.resolutions[0].status, STATUS_STALE)
        with self.assertRaises(RuntimeError):
            assert_fail_closed(report)

    def test_digest_is_deterministic(self):
        claims=[Claim("a","x","y","z","github","2026-09-09T08:00:00Z",True,"canonical","sha:a")]
        self.assertEqual(self.r.reconcile(claims, NOW).canonical_digest(), self.r.reconcile(claims, NOW).canonical_digest())

if __name__ == "__main__":
    unittest.main(verbosity=2)
