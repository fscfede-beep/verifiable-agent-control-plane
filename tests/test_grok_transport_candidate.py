import unittest

import verifiable_agent_control_plane as vacp


class GrokTransportCandidateContractTests(unittest.TestCase):
    def test_candidate_identity_is_explicit_and_never_authority_or_production(self):
        candidate_type = getattr(vacp, "TransportCandidate", None)
        self.assertIsNotNone(candidate_type, "TransportCandidate public API is missing")

        candidate = candidate_type(node_id="GROK_BUILD_PRIMARY")
        self.assertEqual(candidate.status, "CANDIDATE")
        self.assertFalse(candidate.is_authority)
        self.assertFalse(candidate.is_production)
        self.assertEqual(candidate.node_id, "GROK_BUILD_PRIMARY")


if __name__ == "__main__":
    unittest.main()
