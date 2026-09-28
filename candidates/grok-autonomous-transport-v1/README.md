# RUMBO_GROK_AUTONOMOUS_TRANSPORT_CANDIDATE_V1

Status: **CANDIDATE ONLY — NOT AUTHORITY — NOT PRODUCTION**

## Scope

This candidate adds a local, deterministic validation and evidence layer for a future
Grok-to-OpenAI transport. It does **not** establish a live autonomous provider-to-provider
connection.

The frozen Grok evidence chain remains separate:

- `97017a374f80c32688c6e67003ef6e93181b5ac8`
- `834e74a48ace7865b3501bf7d495c296a35198ee`
- `f74be2f68fbac30190b5105d19e99a1153b85eec`
- branch `federation/grok-build-primary`

Those objects are not modified by this candidate.

## Implemented candidate gates

- explicit `GROK_BUILD_PRIMARY` node identity;
- fixed schema `rumbo-grok-transport-envelope-v1`;
- allowlisted message kinds and target node;
- human-controlled gate disabled by default;
- replay protection by nonce;
- duplicate message-id rejection;
- idempotent retry only when the exact same envelope digest is reused;
- idempotency-key conflict rejection for a different envelope;
- secret-like payload-key rejection;
- canonical JSON hashing;
- SHA-256-bound receipts;
- append-only receipt chaining in immutable candidate state;
- tamper detection;
- explicit `CANDIDATE`, `is_authority=False`, `is_production=False`.

## Non-goals / not proven

This candidate does not prove:

- live Grok API connectivity;
- live OpenAI inbound connectivity;
- autonomous machine-to-machine transport;
- MCP bridge;
- inbound webhook;
- cryptographic node identity;
- external durable storage;
- distributed consensus;
- control-plane promotion;
- production readiness;
- end-to-end federation.

The current implementation performs no network I/O.

## Test evidence

TDD RED:
- run `36384108573`
- expected failure: missing candidate transport security API.

GREEN:
- subject SHA: `e52a1c7be5e42658f29ca16bde0456ad977b4269`
- run `36384236596`
- Python 3.11 / 3.12 / 3.13: install, quickstart, full unit suite, outside-checkout import all passed.

## Next gate

A separate authorization is required before adding a real provider transport adapter.
That future adapter must preserve this fail-closed contract and must not promote itself
to authority or production.
