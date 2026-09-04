import unittest

import verifiable_agent_control_plane as package
import verifiable_control_plane as legacy


class PackageSurfaceTests(unittest.TestCase):
    def test_public_package_exposes_core_api(self):
        self.assertTrue(callable(package.decide))
        self.assertTrue(callable(package.materialize))
        self.assertTrue(callable(package.verify_transition))

    def test_public_package_exposes_agent_security_api(self):
        expected = (
            "ActionGrant",
            "ApprovalAnchor",
            "ApprovalEvidence",
            "ContextArtifact",
            "Delegation",
            "Principal",
            "SecurityDecision",
            "SecurityPolicy",
            "SecurityReceipt",
            "evaluate_security",
            "secure_materialize",
            "verify_security_transition",
        )
        for name in expected:
            with self.subTest(name=name):
                self.assertTrue(hasattr(package, name), name)

    def test_legacy_module_is_a_compatibility_shim(self):
        self.assertIs(legacy.materialize, package.materialize)
        self.assertIs(legacy.verify_transition, package.verify_transition)


if __name__ == "__main__":
    unittest.main()
