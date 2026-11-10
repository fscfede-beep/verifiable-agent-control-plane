from __future__ import annotations

import sys

from verifiable_agent_control_plane import (
    CanonicalState,
    ControlPlaneError,
    EffectResult,
    InMemoryTarget,
    Intent,
    Policy,
    Receipt,
    decide,
    materialize,
    verify_transition,
)


def run_verified_transition() -> tuple[CanonicalState, Receipt, EffectResult]:
    state = CanonicalState()
    policy = Policy(frozenset({"set_value"}))
    intent = Intent(
        intent_id="quickstart-verified",
        expected_revision=0,
        expected_checkpoint="ZERO",
        action="set_value",
        payload={"key": "mode", "value": "safe"},
    )
    decision = decide(intent, state, policy)
    target = InMemoryTarget()
    next_state, receipt, effect = materialize(
        intent=intent,
        decision=decision,
        state=state,
        policy=policy,
        execute=target.execute,
    )
    verify_transition(
        prior_state=state,
        next_state=next_state,
        intent=intent,
        receipt=receipt,
        effect=effect,
    )
    return next_state, receipt, effect


def run_state_drift_rejection() -> tuple[str, dict[str, object]]:
    state = CanonicalState()
    policy = Policy(frozenset({"set_value"}))
    stale_intent = Intent(
        intent_id="quickstart-stale",
        expected_revision=0,
        expected_checkpoint="ZERO",
        action="set_value",
        payload={"key": "mode", "value": "blocked"},
    )
    stale_decision = decide(stale_intent, state, policy)
    advance_intent = Intent(
        intent_id="quickstart-advance",
        expected_revision=0,
        expected_checkpoint="ZERO",
        action="set_value",
        payload={"key": "mode", "value": "advanced"},
    )
    advance_decision = decide(advance_intent, state, policy)
    advanced_state, _, _ = materialize(
        intent=advance_intent,
        decision=advance_decision,
        state=state,
        policy=policy,
        execute=InMemoryTarget().execute,
    )

    blocked_target = InMemoryTarget()
    try:
        materialize(
            intent=stale_intent,
            decision=stale_decision,
            state=advanced_state,
            policy=policy,
            execute=blocked_target.execute,
        )
    except ControlPlaneError as exc:
        reason = str(exc)
    else:
        raise RuntimeError("stale decision unexpectedly materialized")

    if reason != "state drift after decision":
        raise RuntimeError(f"unexpected rejection reason: {reason}")
    if blocked_target.values:
        raise RuntimeError("blocked target mutated")
    return reason, dict(blocked_target.values)


def main() -> int:
    try:
        next_state, receipt, effect = run_verified_transition()
        print("PASS verified transition")
        print(f"  revision=0->{next_state.revision}")
        print(f"  checkpoint={next_state.checkpoint}")
        print(f"  observed={dict(effect.observed_payload)}")
        print(f"  receipt_sha256={receipt.receipt_hash}")

        reason, blocked_values = run_state_drift_rejection()
        print(f"FAIL-CLOSED {reason}")
        print(f"  blocked_target_mutated={bool(blocked_values)}")
        return 0
    except Exception as exc:
        print(f"ERROR quickstart failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
