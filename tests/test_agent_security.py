import unittest

from verifiable_agent_control_plane import CanonicalState, Intent
from verifiable_agent_control_plane.security import (
    ActionGrant,
    ContextArtifact,
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

    def _grant(self, resources=frozenset({"record:a"})):
        return SecurityPolicy(
            grants=(ActionGrant("user-a", "set_value", resources),)
        )

    def _delegation(self, resources=frozenset({"record:a"}), **kwargs):
        return Delegation(
            delegation_id=kwargs.get("delegation_id", "delegation-1"),
            delegator_principal_id=kwargs.get("delegator", "user-a"),
            delegate_principal_id=kwargs.get("delegate", "service-agent"),
            allowed_actions=kwargs.get("allowed_actions", frozenset({"set_value"})),
            resource_scope=resources,
            active=kwargs.get("active", True),
            expires_at_epoch=kwargs.get("expires_at_epoch"),
        )

    def test_s01_confused_deputy_cannot_exceed_requester_resource_scope(self):
        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(frozenset({"record:a", "record:b"})),
            policy=self._grant(frozenset({"record:a"})),
            state=self.state,
            requested_resources=frozenset({"record:b"}),
            evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "resource outside principal scope")

    def test_s02_reference_grafting_outside_delegation_is_rejected(self):
        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(frozenset({"record:a"})),
            policy=self._grant(frozenset({"record:a", "record:b"})),
            state=self.state,
            requested_resources=frozenset({"record:b"}),
            evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "resource outside delegation scope")

    def test_exact_principal_delegation_and_resource_scope_is_accepted(self):
        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(expires_at_epoch=200),
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "accepted")

    def test_s03_poisoned_tool_metadata_cannot_mint_authority(self):
        poisoned = ContextArtifact(
            artifact_id="tool-1",
            source_type="mcp_tool_metadata",
            source_id="synthetic-tool",
            trust_class="untrusted",
            content_digest="attacker-controlled-delete-instruction",
        )
        intent = Intent(
            intent_id="security-intent-poisoned-tool",
            expected_revision=0,
            expected_checkpoint="ZERO",
            action="delete_value",
            payload={"key": "mode"},
        )
        decision = evaluate_security(
            intent=intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(
                allowed_actions=frozenset({"set_value", "delete_value"})
            ),
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            artifacts=(poisoned,),
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "principal not permitted for action")

    def test_s04_agent_to_agent_carrier_requires_receiver_authority(self):
        receiver = Principal("agent-b", "agent", "tenant-1")
        carrier = ContextArtifact(
            artifact_id="shared-channel-1",
            source_type="agent_shared_channel",
            source_id="agent-a",
            trust_class="untrusted",
            content_digest="propagated-call-set-value",
        )
        delegation = self._delegation(delegator="agent-b")
        decision = evaluate_security(
            intent=self.intent,
            requester=receiver,
            executor=self.executor,
            delegation=delegation,
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            artifacts=(carrier,),
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "principal not permitted for action")

    def test_s07_untrusted_telemetry_is_bound_as_provenance_not_authority(self):
        telemetry_a = ContextArtifact(
            artifact_id="telemetry-a",
            source_type="telemetry",
            source_id="synthetic-log",
            trust_class="untrusted",
            content_digest="log-field-with-injected-instruction",
        )
        telemetry_b = ContextArtifact(
            artifact_id="telemetry-b",
            source_type="telemetry",
            source_id="synthetic-log-2",
            trust_class="unknown",
            content_digest="second-log-record",
        )
        first = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(),
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            artifacts=(telemetry_a, telemetry_b),
        )
        reordered = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(),
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            artifacts=(telemetry_b, telemetry_a),
        )
        self.assertTrue(first.accepted)
        self.assertEqual(first.provenance_digest, reordered.provenance_digest)
        self.assertTrue(first.provenance_digest)


if __name__ == "__main__":
    unittest.main()
