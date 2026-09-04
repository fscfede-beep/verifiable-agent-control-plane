import unittest
from dataclasses import replace

from verifiable_agent_control_plane import (
    CanonicalState,
    ControlPlaneError,
    EffectResult,
    InMemoryTarget,
    Intent,
    Policy,
    decide,
)
from verifiable_agent_control_plane.security import (
    ActionGrant,
    ApprovalEvidence,
    ContextArtifact,
    Delegation,
    Principal,
    SecurityPolicy,
    evaluate_security,
    secure_materialize,
    verify_security_transition,
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
        self.core_policy = Policy(frozenset({"set_value"}))

    def _grant(self, resources=frozenset({"record:a"}), approval_required=False):
        return SecurityPolicy(
            grants=(ActionGrant("user-a", "set_value", resources),),
            approval_required_actions=(
                frozenset({"set_value"}) if approval_required else frozenset()
            ),
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

    def _security_decision(
        self,
        *,
        delegation=None,
        policy=None,
        requester=None,
        executor=None,
        artifacts=(),
        approval=None,
    ):
        return evaluate_security(
            intent=self.intent,
            requester=requester or self.requester,
            executor=executor or self.executor,
            delegation=delegation or self._delegation(),
            policy=policy or self._grant(),
            state=self.state,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            artifacts=artifacts,
            approval=approval,
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
        decision = evaluate_security(
            intent=self.intent,
            requester=receiver,
            executor=self.executor,
            delegation=self._delegation(delegator="agent-b"),
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
        first = self._security_decision(artifacts=(telemetry_a, telemetry_b))
        reordered = self._security_decision(artifacts=(telemetry_b, telemetry_a))
        self.assertTrue(first.accepted)
        self.assertEqual(first.provenance_digest, reordered.provenance_digest)
        self.assertTrue(first.provenance_digest)

    def test_s05_delegation_drift_is_rejected_before_execution(self):
        delegation = self._delegation()
        security_decision = self._security_decision(delegation=delegation)
        core_decision = decide(self.intent, self.state, self.core_policy)
        target = InMemoryTarget()

        with self.assertRaisesRegex(
            ControlPlaneError,
            "security context no longer accepted: delegation inactive",
        ):
            secure_materialize(
                intent=self.intent,
                core_decision=core_decision,
                security_decision=security_decision,
                state=self.state,
                core_policy=self.core_policy,
                requester=self.requester,
                executor=self.executor,
                delegation=replace(delegation, active=False),
                security_policy=self._grant(),
                requested_resources=frozenset({"record:a"}),
                evaluation_epoch=100,
                execute=target.execute,
            )

        self.assertEqual(target.values, {})

    def test_s06_action_substitution_still_fails_closed(self):
        security_decision = self._security_decision()
        core_decision = decide(self.intent, self.state, self.core_policy)

        def substituted_execute(action, payload):
            return EffectResult(
                effect_id="substituted-effect",
                action="delete_value",
                requested_payload=dict(payload),
                observed_payload=dict(payload),
            )

        with self.assertRaisesRegex(ControlPlaneError, "effect action mismatch"):
            secure_materialize(
                intent=self.intent,
                core_decision=core_decision,
                security_decision=security_decision,
                state=self.state,
                core_policy=self.core_policy,
                requester=self.requester,
                executor=self.executor,
                delegation=self._delegation(),
                security_policy=self._grant(),
                requested_resources=frozenset({"record:a"}),
                evaluation_epoch=100,
                execute=substituted_execute,
            )

    def test_s08_sensitive_approval_requires_independent_verification_digest(self):
        policy = self._grant(approval_required=True)
        approval = ApprovalEvidence(
            approval_id="approval-1",
            intent_digest=self.intent.digest,
            principal_id="user-a",
            action="set_value",
            approved=True,
            verification_digest=None,
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "independent verification required")

    def test_s09_tool_metadata_rug_pull_is_detected_before_execution(self):
        original = ContextArtifact(
            artifact_id="tool-1",
            source_type="mcp_tool_metadata",
            source_id="synthetic-tool",
            trust_class="untrusted",
            content_digest="metadata-v1",
        )
        changed = replace(original, content_digest="metadata-v2")
        security_decision = self._security_decision(artifacts=(original,))
        core_decision = decide(self.intent, self.state, self.core_policy)
        target = InMemoryTarget()

        with self.assertRaisesRegex(ControlPlaneError, "security context drift after decision"):
            secure_materialize(
                intent=self.intent,
                core_decision=core_decision,
                security_decision=security_decision,
                state=self.state,
                core_policy=self.core_policy,
                requester=self.requester,
                executor=self.executor,
                delegation=self._delegation(),
                security_policy=self._grant(),
                requested_resources=frozenset({"record:a"}),
                evaluation_epoch=100,
                artifacts=(changed,),
                execute=target.execute,
            )

        self.assertEqual(target.values, {})

    def test_security_receipt_verifies_for_same_context(self):
        delegation = self._delegation()
        policy = self._grant()
        security_decision = self._security_decision(delegation=delegation, policy=policy)
        core_decision = decide(self.intent, self.state, self.core_policy)
        target = InMemoryTarget()

        next_state, core_receipt, security_receipt, effect = secure_materialize(
            intent=self.intent,
            core_decision=core_decision,
            security_decision=security_decision,
            state=self.state,
            core_policy=self.core_policy,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            security_policy=policy,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            execute=target.execute,
        )

        verify_security_transition(
            prior_state=self.state,
            next_state=next_state,
            intent=self.intent,
            core_receipt=core_receipt,
            security_receipt=security_receipt,
            effect=effect,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            security_policy=policy,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
        )

    def test_s10_security_receipt_cannot_be_replayed_under_another_principal(self):
        delegation = self._delegation()
        policy = self._grant()
        security_decision = self._security_decision(delegation=delegation, policy=policy)
        core_decision = decide(self.intent, self.state, self.core_policy)
        target = InMemoryTarget()
        next_state, core_receipt, security_receipt, effect = secure_materialize(
            intent=self.intent,
            core_decision=core_decision,
            security_decision=security_decision,
            state=self.state,
            core_policy=self.core_policy,
            requester=self.requester,
            executor=self.executor,
            delegation=delegation,
            security_policy=policy,
            requested_resources=frozenset({"record:a"}),
            evaluation_epoch=100,
            execute=target.execute,
        )
        other_requester = Principal("user-b", "human", "tenant-1")

        with self.assertRaisesRegex(ControlPlaneError, "security requester mismatch"):
            verify_security_transition(
                prior_state=self.state,
                next_state=next_state,
                intent=self.intent,
                core_receipt=core_receipt,
                security_receipt=security_receipt,
                effect=effect,
                requester=other_requester,
                executor=self.executor,
                delegation=delegation,
                security_policy=policy,
                requested_resources=frozenset({"record:a"}),
                evaluation_epoch=100,
            )


    def test_empty_requested_resources_fail_closed(self):
        decision = evaluate_security(
            intent=self.intent,
            requester=self.requester,
            executor=self.executor,
            delegation=self._delegation(),
            policy=self._grant(),
            state=self.state,
            requested_resources=frozenset(),
            evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "resource scope required")
if __name__ == "__main__":
    unittest.main()
