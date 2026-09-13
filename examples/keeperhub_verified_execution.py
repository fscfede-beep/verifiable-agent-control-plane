#!/usr/bin/env python3
"""Bounded KeeperHub demo for the Verifiable Agent Control Plane.

Safe default: only GET /api/chains is called. Authenticated workflow listing or
execution requires explicit CLI flags. No direct on-chain broadcast path exists.
"""

from __future__ import annotations

import argparse
import json

from verifiable_agent_control_plane.keeperhub import KeeperHubClient, KeeperHubError


def _print(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-workflows", action="store_true")
    parser.add_argument("--execute-workflow")
    parser.add_argument("--allow-execution", action="store_true")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()

    client = KeeperHubClient()

    try:
        chains, chains_receipt = client.probe_chains()
        _print(
            {
                "public_probe": "PASS",
                "enabled_testnets": [
                    chain
                    for chain in chains
                    if chain.get("isEnabled") is True and chain.get("isTestnet") is True
                ],
                "receipt": chains_receipt.as_dict(),
            }
        )

        if args.list_workflows:
            workflows, workflows_receipt = client.list_workflows()
            _print(
                {
                    "workflow_count": len(workflows),
                    "workflows": [
                        {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "active": item.get("active"),
                        }
                        for item in workflows
                    ],
                    "receipt": workflows_receipt.as_dict(),
                }
            )

        if args.execute_workflow:
            if not args.allow_execution:
                raise KeeperHubError(
                    "execution_not_authorized",
                    "Pass --allow-execution to authorize one workflow execution",
                )
            response, execution_receipt = client.execute_workflow(
                args.execute_workflow,
                allow_execution=True,
            )
            _print({"execution": response, "receipt": execution_receipt.as_dict()})

            if args.wait:
                result, wait_receipt = client.wait_for_execution(response["executionId"])
                client.require_success(result)
                _print({"final": result, "receipt": wait_receipt.as_dict()})

        return 0
    except KeeperHubError as exc:
        _print(
            {
                "state": "SAFE_STOP",
                "error": exc.code,
                "detail": exc.detail,
                "request_id": exc.request_id,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
