import json
import unittest
import urllib.error

from verifiable_agent_control_plane.keeperhub import KeeperHubClient, KeeperHubError


class FakeResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class QueueOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        payload, headers = self.responses.pop(0)
        return FakeResponse(payload, headers)


class TransportFailureOpener:
    def __init__(self):
        self.calls = 0

    def __call__(self, request, timeout):
        self.calls += 1
        raise urllib.error.URLError("connection dropped")


class KeeperHubClientTests(unittest.TestCase):
    def test_public_chain_probe_needs_no_api_key(self):
        opener = QueueOpener([([{"chainId": 84532, "isTestnet": True}], {"x-request-id": "r1"})])
        client = KeeperHubClient(opener=opener)
        chains, receipt = client.probe_chains()
        request, _ = opener.requests[0]

        self.assertEqual(chains[0]["chainId"], 84532)
        self.assertEqual(request.method, "GET")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(receipt.request_id, "r1")

    def test_private_workflow_listing_fails_closed_without_key(self):
        client = KeeperHubClient(opener=QueueOpener([]))
        with self.assertRaises(KeeperHubError) as ctx:
            client.list_workflows()
        self.assertEqual(ctx.exception.code, "missing_api_key")

    def test_execution_requires_explicit_authorization(self):
        client = KeeperHubClient(api_key="kh_test", opener=QueueOpener([]))
        with self.assertRaises(KeeperHubError) as ctx:
            client.execute_workflow("wf_123")
        self.assertEqual(ctx.exception.code, "execution_not_authorized")

    def test_execution_returns_hashed_receipt(self):
        opener = QueueOpener(
            [({"executionId": "exec_123", "status": "running"}, {"x-request-id": "r2"})]
        )
        client = KeeperHubClient(api_key="kh_test", opener=opener)
        response, receipt = client.execute_workflow(
            "wf_123",
            input_data={"message": "hello"},
            allow_execution=True,
        )

        request, _ = opener.requests[0]
        self.assertEqual(response["executionId"], "exec_123")
        self.assertEqual(receipt.execution_id, "exec_123")
        self.assertEqual(receipt.request_id, "r2")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer kh_test")
        self.assertEqual(len(receipt.request_sha256), 64)
        self.assertEqual(len(receipt.response_sha256), 64)

    def test_one_execution_ceiling(self):
        opener = QueueOpener([({"executionId": "exec_1", "status": "running"}, {})])
        client = KeeperHubClient(api_key="kh_test", opener=opener)
        client.execute_workflow("wf_1", allow_execution=True)

        with self.assertRaises(KeeperHubError) as ctx:
            client.execute_workflow("wf_2", allow_execution=True)
        self.assertEqual(ctx.exception.code, "execution_budget_exhausted")

    def test_transport_failure_consumes_execution_budget(self):
        opener = TransportFailureOpener()
        client = KeeperHubClient(api_key="kh_test", opener=opener)

        with self.assertRaises(KeeperHubError) as transport:
            client.execute_workflow("wf_1", allow_execution=True)
        self.assertEqual(transport.exception.code, "transport_error")
        self.assertEqual(opener.calls, 1)

        with self.assertRaises(KeeperHubError) as replay:
            client.execute_workflow("wf_1", allow_execution=True)
        self.assertEqual(replay.exception.code, "execution_budget_exhausted")
        self.assertEqual(opener.calls, 1)

    def test_missing_key_does_not_consume_execution_budget(self):
        opener = QueueOpener([({"executionId": "exec_1", "status": "running"}, {})])
        client = KeeperHubClient(opener=opener)

        with self.assertRaises(KeeperHubError) as missing:
            client.execute_workflow("wf_1", allow_execution=True)
        self.assertEqual(missing.exception.code, "missing_api_key")

        client._api_key = "kh_test"
        response, _ = client.execute_workflow("wf_1", allow_execution=True)
        self.assertEqual(response["executionId"], "exec_1")

    def test_wait_requires_success_before_claiming_completion(self):
        client = KeeperHubClient(api_key="kh_test", opener=QueueOpener([]))
        with self.assertRaises(KeeperHubError) as incomplete:
            client.require_success({"completed": False, "status": "running"})
        self.assertEqual(incomplete.exception.code, "execution_incomplete")

        with self.assertRaises(KeeperHubError) as failed:
            client.require_success({"completed": True, "status": "cancelled"})
        self.assertEqual(failed.exception.code, "execution_failed")

        successful = {"completed": True, "status": "success", "transactionHashes": []}
        self.assertIs(client.require_success(successful), successful)

    def test_transfer_helper_matches_rest_schema_and_is_simulation_only(self):
        payload = KeeperHubClient.build_transfer_simulation(
            chain_id=84532,
            to_address="0x1111111111111111111111111111111111111111",
            amount="0.01",
        )
        self.assertEqual(
            payload["recipientAddress"],
            "0x1111111111111111111111111111111111111111",
        )
        self.assertNotIn("toAddress", payload)
        self.assertIs(payload["simulate"], True)
        self.assertFalse(KeeperHubClient.direct_broadcast_supported())


if __name__ == "__main__":
    unittest.main()
