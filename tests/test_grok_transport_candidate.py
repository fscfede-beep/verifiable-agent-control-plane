import unittest

import verifiable_agent_control_plane as vacp


class GrokTransportCandidateContractTests(unittest.TestCase):
    def test_transport_security_surface_is_explicit(self):
        required = (
            "GrokTransportEnvelope",
            "GrokTransportState",
            "HumanKillSwitch",
            "TransportCandidateError",
        )
        missing = [name for name in required if getattr(vacp, name, None) is None]
        self.assertEqual(missing, [], f"missing candidate transport API: {missing}")


if __name__ == "__main__":
    unittest.main()
