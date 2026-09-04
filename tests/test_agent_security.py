import unittest

from verifiable_agent_control_plane import CanonicalState, Intent
from verifiable_agent_control_plane.security import (
    ActionGrant,
    Delegation,
    Principal,
    SecurityPolicy,
    evaluate_security,
)


class AgentSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = CanonicalState()
        self.requester = Principal("user-a", "human", "tenant-1")
        self.executor = Principal("service-agent", "service", "tenant-1")
        self.intent = Intent(
            intent_id="security-intent-001",
            expected_revision=0,
            expected_checkpoint="ZERO",
            action="set_value",
            payload={"key": "mode", "value": "safe"},
        )

    def test_s01_confused_deputy_cannot_exceed_requester_resource_scope(self):
        policy = SecurityPolicy(
            grants=(ActionGrant("user-a", "set_value", frozenset({"record:a"})),)
        )
        delegation = Delegation(
            delegation_id="delegation-1",
            delegator_principal_id="user-a",
            delegate_principal_id="service-agent",
            allowed_actions=frozenset({"set_value"}),
            resource_scope=frozenset({"record:a", "record:b"}),
        )

        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            policy=policy,
            state=self.state,
            requested_resources=frozenset({"record:b"}),
            evaluation_epoch=100,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "resource outside principal scope")

    def test_s02_reference_grafting_outside_delegation_is_rejected(self):
        policy = SecurityPolicy(
            grants=(
                ActionGrant("user-a", "set_value", frozenset({"record:a", "record:b"})),
            )
        )
        delegation = Delegation(
            delegation_id="delegation-2",
            delegator_principal_id="user-a",
            delegate_principal_id="service-agent",
            allowed_actions=frozenset({"set_value"}),
            resource_scope=frozenset({"record:a"}),
        )

        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            policy=policy,
            state=self.state,
            requested_resources=frozenset({"record:b"}),
            evaluation_epoch=100,
        )

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "resource outside delegation scope")

    def test_exact_principal_delegation_and_resource_scope_is_accepted(self):
        policy = SecurityPolicy(
            grants=(ActionGrant("user-a", "set_value", frozenset({"record:a"})),)
        )
        delegation = Delegation(
            delegation_id="delegation-3",
            delegator_principal_id="user-a",
            delegate_principal_id="service-agent",
            allowed_actions=frozenset({"set_value"}),
            resource_scope=frozenset({"record:a"}),
            active=True,
            expires_at_epoch=200,
        )

        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            policy=policy,
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "accepted")


if __name__ == "__main__":
    unittest.main()
