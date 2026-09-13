#!/usr/bin/env python3
"""RUMBO Voice Recovery Agent — CALL-E adapter.

Dry-run by default. Live phone calls require:
  --live
  --confirm "PLACE CALL"
  CALLE_API_KEY
  --phone <authorized E.164 number>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
LIVE_CONFIRMATION = "PLACE CALL"
DEFAULT_TASK = (
    "You are the RUMBO Voice Recovery Agent. Call the authorized recipient, "
    "clearly identify that this is an AI-assisted call on behalf of RUMBO IA, "
    "and ask only whether they want a human follow-up about the pending business "
    "conversation. Do not request passwords, one-time codes, financial secrets, "
    "payment-card data, medical information, or legal advice. "
    "Return only the bounded outcome requested by the structured schema."
)

RECIPIENT_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["contact_status", "intent", "next_action"],
    "additionalProperties": False,
    "properties": {
        "contact_status": {
            "type": "string",
            "enum": ["reached", "not_reached", "wrong_number", "unknown"],
        },
        "intent": {
            "type": "string",
            "enum": ["interested", "not_interested", "callback_requested", "unknown"],
        },
        "next_action": {
            "type": "string",
            "enum": ["human_follow_up", "schedule_callback", "close", "none"],
        },
        "preferred_time": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
    },
}

CALL_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["completed_count"],
    "additionalProperties": False,
    "properties": {
        "completed_count": {"type": "integer", "minimum": 0},
    },
}


@dataclass(frozen=True)
class CallPlan:
    phone: str
    task: str
    locale: str
    region: str
    workflow_id: str

    @property
    def phone_fingerprint(self) -> str:
        return hashlib.sha256(self.phone.encode("utf-8")).hexdigest()[:12]

    @property
    def idempotency_key(self) -> str:
        material = f"{self.workflow_id}|{self.phone}|{self.task}".encode("utf-8")
        return "rumbo-recovery-" + hashlib.sha256(material).hexdigest()[:32]


def validate_e164(phone: str) -> str:
    if not E164_RE.fullmatch(phone):
        raise ValueError("phone must be E.164, for example +14155550123")
    return phone


def build_plan(
    phone: str,
    *,
    task: str = DEFAULT_TASK,
    locale: str = "es-AR",
    region: str = "AR",
    workflow_id: str | None = None,
) -> CallPlan:
    validate_e164(phone)
    if not task.strip():
        raise ValueError("task must not be empty")
    workflow_id = workflow_id or f"manual-{int(time.time())}"
    return CallPlan(
        phone=phone,
        task=task.strip(),
        locale=locale,
        region=region,
        workflow_id=workflow_id,
    )


def redacted_preview(plan: CallPlan) -> dict[str, Any]:
    return {
        "mode": "dry-run",
        "phone_fingerprint": plan.phone_fingerprint,
        "locale": plan.locale,
        "region": plan.region,
        "workflow_id": plan.workflow_id,
        "idempotency_key": plan.idempotency_key,
        "task": plan.task,
        "result_schema": CALL_RESULT_SCHEMA,
        "recipient_result_schema": RECIPIENT_RESULT_SCHEMA,
        "safety": {
            "live_requires_explicit_confirmation": LIVE_CONFIRMATION,
            "api_key_logged": False,
            "phone_logged": False,
            "consequential_action": "human_approval_required",
        },
    }


def run_live(plan: CallPlan) -> dict[str, Any]:
    api_key = os.environ.get("CALLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("CALLE_API_KEY is required for --live")

    try:
        from calle import CalleClient
    except ImportError as exc:
        raise RuntimeError(
            "CALL-E SDK not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    base_url = os.environ.get("CALLE_BASE_URL", "https://api.heycall-e.com").strip()

    with CalleClient(api_key=api_key, base_url=base_url) as client:
        call = client.calls.create_and_wait(
            task=plan.task,
            recipients=[
                {
                    "phones": [plan.phone],
                    "region": plan.region,
                    "locale": plan.locale,
                }
            ],
            result_schema=CALL_RESULT_SCHEMA,
            recipient_result_schema=RECIPIENT_RESULT_SCHEMA,
            metadata={
                "workflow_id": plan.workflow_id,
                "source": "rumbo-voice-recovery-v1",
                "human_control": True,
            },
            idempotency_key=plan.idempotency_key,
        )

    recipient = (call.get("recipients") or [{}])[0]
    return {
        "mode": "live",
        "call_id": call.get("id"),
        "status": call.get("status"),
        "task_completed": call.get("task_completed"),
        "completion_confidence": call.get("completion_confidence"),
        "structured_result": call.get("structured_result"),
        "recipient_result": recipient.get("structured_result"),
        "evidence": call.get("evidence"),
        "phone_fingerprint": plan.phone_fingerprint,
        "idempotency_key": plan.idempotency_key,
        "human_approval_required_for_next_action": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RUMBO Voice Recovery Agent")
    parser.add_argument("--phone", required=True, help="authorized recipient in E.164")
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--locale", default="es-AR")
    parser.add_argument("--region", default="AR")
    parser.add_argument("--workflow-id")
    parser.add_argument("--live", action="store_true", help="allow a real CALL-E call")
    parser.add_argument(
        "--confirm",
        default="",
        help=f'live-mode confirmation; must equal "{LIVE_CONFIRMATION}"',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        plan = build_plan(
            args.phone,
            task=args.task,
            locale=args.locale,
            region=args.region,
            workflow_id=args.workflow_id,
        )

        if not args.live:
            print(json.dumps(redacted_preview(plan), indent=2, ensure_ascii=False))
            return 0

        if args.confirm != LIVE_CONFIRMATION:
            raise RuntimeError(
                f'live call blocked: pass --confirm "{LIVE_CONFIRMATION}" exactly'
            )

        result = run_live(plan)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
