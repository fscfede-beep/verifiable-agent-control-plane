from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

BASE_URL = "https://app.keeperhub.com"
TERMINAL_SUCCESS = "success"


class KeeperHubError(RuntimeError):
    def __init__(self, code: str, detail: str, request_id: str | None = None):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.request_id = request_id


@dataclass(frozen=True)
class KeeperHubReceipt:
    operation: str
    endpoint: str
    request_sha256: str
    response_sha256: str
    request_id: str | None
    execution_id: str | None
    status: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "endpoint": self.endpoint,
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "request_id": self.request_id,
            "execution_id": self.execution_id,
            "status": self.status,
        }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class KeeperHubClient:
    """Bounded KeeperHub client for verifiable agent execution.

    The client deliberately exposes workflow execution but no direct on-chain
    broadcast method. Direct-transfer helpers can only construct simulation
    payloads. Live workflow execution requires both an API key and explicit
    per-call authorization.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout_seconds: float = 15.0,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
    ):
        self._api_key = api_key or os.getenv("KEEPERHUB_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opener = opener or self._default_open
        self._execution_count = 0

    @staticmethod
    def _default_open(req: urllib.request.Request, timeout: float):
        return urllib.request.urlopen(req, timeout=timeout)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        auth_required: bool,
    ) -> tuple[dict[str, Any] | list[Any], dict[str, str]]:
        if auth_required and not self._api_key:
            raise KeeperHubError("missing_api_key", "KEEPERHUB_API_KEY is required")

        payload = None if body is None else _canonical(body)
        headers = {
            "Accept": "application/json",
            "User-Agent": "verifiable-agent-control-plane/keeperhub-demo",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if auth_required:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=payload,
            headers=headers,
            method=method,
        )
        try:
            response = self._opener(req, self.timeout_seconds)
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
            response_headers = {k.lower(): v for k, v in dict(response.headers).items()}
            return parsed, response_headers
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                parsed = {}
            code = parsed.get("error", f"http_{exc.code}")
            detail = parsed.get("detail", "KeeperHub request failed")
            request_id = parsed.get("request_id") or exc.headers.get("x-request-id")
            raise KeeperHubError(code, detail, request_id) from exc

    def probe_chains(self) -> tuple[list[dict[str, Any]], KeeperHubReceipt]:
        response, headers = self._request("GET", "/api/chains", auth_required=False)
        if not isinstance(response, list):
            raise KeeperHubError("invalid_response", "GET /api/chains did not return a list")
        receipt = self._receipt("probe_chains", "/api/chains", None, response, headers)
        return response, receipt

    def list_workflows(self) -> tuple[list[dict[str, Any]], KeeperHubReceipt]:
        response, headers = self._request("GET", "/api/workflows", auth_required=True)
        if not isinstance(response, list):
            raise KeeperHubError("invalid_response", "GET /api/workflows did not return a list")
        receipt = self._receipt("list_workflows", "/api/workflows", None, response, headers)
        return response, receipt

    def execute_workflow(
        self,
        workflow_id: str,
        *,
        input_data: dict[str, Any] | None = None,
        allow_execution: bool = False,
    ) -> tuple[dict[str, Any], KeeperHubReceipt]:
        if not allow_execution:
            raise KeeperHubError(
                "execution_not_authorized",
                "Workflow execution requires allow_execution=True",
            )
        if self._execution_count >= 1:
            raise KeeperHubError(
                "execution_budget_exhausted",
                "Only one workflow execution is allowed per client instance",
            )
        if not workflow_id.strip():
            raise KeeperHubError("invalid_workflow_id", "workflow_id must be non-empty")

        path = f"/api/workflows/{urllib.parse.quote(workflow_id, safe='')}/execute"
        body = {"input": input_data or {}}
        response, headers = self._request("POST", path, body=body, auth_required=True)
        if not isinstance(response, dict) or not response.get("executionId"):
            raise KeeperHubError("missing_execution_id", "Execution response omitted executionId")
        self._execution_count += 1
        return response, self._receipt("execute_workflow", path, body, response, headers)

    def wait_for_execution(
        self,
        execution_id: str,
        *,
        timeout_ms: int = 25_000,
    ) -> tuple[dict[str, Any], KeeperHubReceipt]:
        if not 1 <= timeout_ms <= 60_000:
            raise KeeperHubError("invalid_timeout", "timeout_ms must be between 1 and 60000")
        encoded_id = urllib.parse.quote(execution_id, safe="")
        path = f"/api/workflows/executions/{encoded_id}/wait?timeoutMs={timeout_ms}"
        response, headers = self._request("GET", path, auth_required=True)
        if not isinstance(response, dict):
            raise KeeperHubError("invalid_response", "Wait endpoint did not return an object")
        return response, self._receipt("wait_for_execution", path, None, response, headers)

    @staticmethod
    def require_success(wait_result: dict[str, Any]) -> dict[str, Any]:
        if not wait_result.get("completed"):
            raise KeeperHubError("execution_incomplete", "Execution has not reached a terminal state")
        if wait_result.get("status") != TERMINAL_SUCCESS:
            raise KeeperHubError(
                "execution_failed",
                str(wait_result.get("error") or f"status={wait_result.get('status')}"),
            )
        return wait_result

    @staticmethod
    def build_transfer_simulation(
        *,
        chain_id: str | int,
        to_address: str,
        amount: str,
        token_address: str | None = None,
    ) -> dict[str, Any]:
        if not str(chain_id).strip() or not to_address.strip() or not amount.strip():
            raise ValueError("chain_id, to_address, and amount are required")
        payload: dict[str, Any] = {
            "chainId": str(chain_id),
            "toAddress": to_address,
            "amount": amount,
            "simulate": True,
        }
        if token_address:
            payload["tokenAddress"] = token_address
        return payload

    @staticmethod
    def direct_broadcast_supported() -> bool:
        return False

    @staticmethod
    def _receipt(
        operation: str,
        endpoint: str,
        request_body: dict[str, Any] | None,
        response_body: Any,
        headers: dict[str, str],
    ) -> KeeperHubReceipt:
        response_id = response_body.get("executionId") if isinstance(response_body, dict) else None
        response_status = response_body.get("status") if isinstance(response_body, dict) else None
        response_request_id = (
            response_body.get("request_id") if isinstance(response_body, dict) else None
        )
        return KeeperHubReceipt(
            operation=operation,
            endpoint=endpoint,
            request_sha256=hashlib.sha256(_canonical(request_body or {})).hexdigest(),
            response_sha256=hashlib.sha256(_canonical(response_body)).hexdigest(),
            request_id=response_request_id or headers.get("x-request-id"),
            execution_id=response_id,
            status=response_status,
        )
