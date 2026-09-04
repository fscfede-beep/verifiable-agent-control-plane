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
    ApprovalAnchor,
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
            grants=(ActionGrant("user-a", "set_value", resources, tenant_id="tenant-1"),),
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
            delegator_tenant_id=kwargs.get("delegator_tenant_id", "tenant-1"),
            delegate_tenant_id=kwargs.get("delegate_tenant_id", "tenant-1"),
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
            tenant_id="tenant-1",
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

    def test_s14_cross_tenant_executor_binding_collision_is_rejected(self):
        requester = Principal("user-a", "human", "tenant-A")
        executor = Principal("service-agent", "service", "tenant-B")
        policy = SecurityPolicy(
            grants=(
                ActionGrant(
                    "user-a", "set_value", frozenset({"record:a"}),
                    tenant_id="tenant-A",
                ),
            )
        )
        delegation = Delegation(
            "delegation-wrong-executor-domain", "user-a", "service-agent",
            frozenset({"set_value"}), frozenset({"record:a"}),
            delegator_tenant_id="tenant-A", delegate_tenant_id="tenant-C",
        )
        decision = evaluate_security(
            intent=self.intent, requester=requester, executor=executor,
            delegation=delegation, policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "delegation executor tenant mismatch")

    def test_s13_cross_tenant_approval_collision_is_rejected(self):
        requester = Principal("user-a", "human", "tenant-B")
        executor = Principal("service-agent", "service", "tenant-B")
        policy = SecurityPolicy(
            grants=(
                ActionGrant(
                    "user-a", "set_value", frozenset({"record:a"}),
                    tenant_id="tenant-B",
                ),
            ),
            approval_required_actions=frozenset({"set_value"}),
        )
        delegation = Delegation(
            "delegation-approval", "user-a", "service-agent",
            frozenset({"set_value"}), frozenset({"record:a"}),
            delegator_tenant_id="tenant-B", delegate_tenant_id="tenant-B",
        )
        approval = ApprovalEvidence(
            approval_id="approval-tenant-A",
            intent_digest=self.intent.digest,
            principal_id="user-a",
            action="set_value",
            approved=True,
            verification_digest="independent-check",
            tenant_id="tenant-A",
        )

        decision = evaluate_security(
            intent=self.intent, requester=requester, executor=executor,
            delegation=delegation, policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
            approval=approval,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval tenant mismatch")

    def test_s11_cross_tenant_grant_collision_is_rejected(self):
        policy = SecurityPolicy(
            grants=(
                ActionGrant(
                    "user-a",
                    "set_value",
                    frozenset({"record:a"}),
                    tenant_id="tenant-A",
                ),
            )
        )
        delegation = Delegation(
            "delegation-cross-tenant",
            "user-a",
            "service-agent",
            frozenset({"set_value"}),
            frozenset({"record:a"}),
            delegator_tenant_id="tenant-B",
            delegate_tenant_id="tenant-B",
        )
        requester = Principal("user-a", "human", "tenant-B")
        executor = Principal("service-agent", "service", "tenant-B")

        decision = evaluate_security(
            intent=self.intent, requester=requester, executor=executor,
            delegation=delegation, policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "principal tenant not permitted for action")

    def test_s12_cross_tenant_delegation_collision_is_rejected(self):
        policy = SecurityPolicy(
            grants=(
                ActionGrant(
                    "user-a",
                    "set_value",
                    frozenset({"record:a"}),
                    tenant_id="tenant-B",
                ),
            )
        )
        delegation = Delegation(
            "delegation-wrong-domain",
            "user-a",
            "service-agent",
            frozenset({"set_value"}),
            frozenset({"record:a"}),
            delegator_tenant_id="tenant-A",
            delegate_tenant_id="tenant-B",
        )
        requester = Principal("user-a", "human", "tenant-B")
        executor = Principal("service-agent", "service", "tenant-B")

        decision = evaluate_security(
            intent=self.intent, requester=requester, executor=executor,
            delegation=delegation, policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "delegation requester tenant mismatch")

    def test_unbound_grant_fails_closed(self):
        policy = SecurityPolicy(
            grants=(ActionGrant("user-a", "set_value", frozenset({"record:a"})),)
        )
        decision = evaluate_security(
            intent=self.intent, requester=self.requester, executor=self.executor,
            delegation=self._delegation(), policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "principal tenant not permitted for action")

    def test_unbound_delegation_fails_closed(self):
        delegation = Delegation(
            "unbound-delegation", "user-a", "service-agent",
            frozenset({"set_value"}), frozenset({"record:a"}),
        )
        decision = evaluate_security(
            intent=self.intent, requester=self.requester, executor=self.executor,
            delegation=delegation, policy=self._grant(), state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "delegation requester tenant mismatch")

    def test_unbound_approval_fails_closed(self):
        policy = self._grant(approval_required=True)
        approval = ApprovalEvidence(
            "unbound-approval", self.intent.digest, "user-a", "set_value",
            True, "independent-check",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval tenant mismatch")

    def test_explicit_cross_tenant_delegation_is_allowed_when_bound(self):
        requester = Principal("user-a", "human", "tenant-A")
        executor = Principal("service-agent", "service", "tenant-B")
        policy = SecurityPolicy(
            grants=(
                ActionGrant(
                    "user-a", "set_value", frozenset({"record:a"}),
                    tenant_id="tenant-A",
                ),
            )
        )
        delegation = Delegation(
            "explicit-cross-tenant", "user-a", "service-agent",
            frozenset({"set_value"}), frozenset({"record:a"}),
            delegator_tenant_id="tenant-A", delegate_tenant_id="tenant-B",
        )
        decision = evaluate_security(
            intent=self.intent, requester=requester, executor=executor,
            delegation=delegation, policy=policy, state=self.state,
            requested_resources=frozenset({"record:a"}), evaluation_epoch=100,
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "accepted")

    def test_security_policy_digest_is_order_independent_across_tenant_grants(self):
        tenant_a = ActionGrant(
            "user-a", "set_value", frozenset({"record:a"}), tenant_id="tenant-A"
        )
        tenant_b = ActionGrant(
            "user-a", "set_value", frozenset({"record:a"}), tenant_id="tenant-B"
        )
        first = SecurityPolicy((tenant_a, tenant_b))
        reversed_order = SecurityPolicy((tenant_b, tenant_a))
        self.assertEqual(first.digest, reversed_order.digest)

    def test_security_authority_models_expose_tenant_bindings(self):
        from inspect import signature

        self.assertIn("tenant_id", signature(ActionGrant).parameters)
        self.assertIn("delegator_tenant_id", signature(Delegation).parameters)
        self.assertIn("delegate_tenant_id", signature(Delegation).parameters)
        self.assertIn("tenant_id", signature(ApprovalEvidence).parameters)

    def test_approval_model_exposes_independent_verifier_bindings(self):
        from inspect import signature

        approval_params = signature(ApprovalEvidence).parameters
        policy_params = signature(SecurityPolicy).parameters
        self.assertIn("verifier_principal_id", approval_params)
        self.assertIn("verifier_tenant_id", approval_params)
        self.assertIn("approval_anchors", policy_params)

    def test_approval_policy_exposes_exact_verification_anchors(self):
        import verifiable_agent_control_plane.security as security_module

        self.assertTrue(hasattr(security_module, "ApprovalAnchor"))

    def test_s15_self_verification_is_rejected(self):
        base = self._grant(approval_required=True)
        anchor = ApprovalAnchor(
            "user-a", "tenant-1", "set_value", self.intent.digest, "self-check"
        )
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
            approval_anchors=(anchor,),
        )
        approval = ApprovalEvidence(
            "approval-self", self.intent.digest, "user-a", "set_value",
            True, "self-check", tenant_id="tenant-1",
            verifier_principal_id="user-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "independent verifier required")

    def test_s16_unanchored_verifier_is_rejected(self):
        base = self._grant(approval_required=True)
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
        )
        approval = ApprovalEvidence(
            "approval-unanchored", self.intent.digest, "user-a", "set_value",
            True, "fabricated-check", tenant_id="tenant-1",
            verifier_principal_id="reviewer-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval evidence not anchored")

    def test_approval_with_digest_but_no_verifier_fails_closed(self):
        policy = self._grant(approval_required=True)
        approval = ApprovalEvidence(
            "approval-unbound-verifier", self.intent.digest, "user-a", "set_value",
            True, "nonempty-check", tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval verifier required")

    def test_trusted_independent_verifier_is_accepted(self):
        base = self._grant(approval_required=True)
        anchor = ApprovalAnchor(
            "reviewer-a", "tenant-1", "set_value",
            self.intent.digest, "independent-check",
        )
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
            approval_anchors=(anchor,),
        )
        approval = ApprovalEvidence(
            "approval-trusted", self.intent.digest, "user-a", "set_value",
            True, "independent-check", tenant_id="tenant-1",
            verifier_principal_id="reviewer-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "accepted")

    def test_s17_executor_cannot_self_verify_approval(self):
        base = self._grant(approval_required=True)
        anchor = ApprovalAnchor(
            "service-agent", "tenant-1", "set_value",
            self.intent.digest, "executor-check",
        )
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
            approval_anchors=(anchor,),
        )
        approval = ApprovalEvidence(
            "approval-executor", self.intent.digest, "user-a", "set_value",
            True, "executor-check", tenant_id="tenant-1",
            verifier_principal_id="service-agent", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "independent verifier required")

    def test_s18_fabricated_verifier_metadata_without_anchor_is_rejected(self):
        base = self._grant(approval_required=True)
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
        )
        approval = ApprovalEvidence(
            "approval-fabricated", self.intent.digest, "user-a", "set_value",
            True, "fabricated-check", tenant_id="tenant-1",
            verifier_principal_id="reviewer-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval evidence not anchored")

    def test_s19_approval_anchor_cannot_be_reused_for_another_intent(self):
        base = self._grant(approval_required=True)
        anchor = ApprovalAnchor(
            "reviewer-a", "tenant-1", "set_value",
            "different-intent-digest", "reviewer-check",
        )
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
            approval_anchors=(anchor,),
        )
        approval = ApprovalEvidence(
            "approval-replay", self.intent.digest, "user-a", "set_value",
            True, "reviewer-check", tenant_id="tenant-1",
            verifier_principal_id="reviewer-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval evidence not anchored")

    def test_s20_approval_anchor_binds_action(self):
        base = self._grant(approval_required=True)
        anchor = ApprovalAnchor(
            "reviewer-a", "tenant-1", "other_action",
            self.intent.digest, "reviewer-check",
        )
        policy = SecurityPolicy(
            grants=base.grants,
            approval_required_actions=base.approval_required_actions,
            approval_anchors=(anchor,),
        )
        approval = ApprovalEvidence(
            "approval-wrong-action-anchor", self.intent.digest,
            "user-a", "set_value", True, "reviewer-check", tenant_id="tenant-1",
            verifier_principal_id="reviewer-a", verifier_tenant_id="tenant-1",
        )
        decision = self._security_decision(policy=policy, approval=approval)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "approval evidence not anchored")


if __name__ == "__main__":
    unittest.main()
