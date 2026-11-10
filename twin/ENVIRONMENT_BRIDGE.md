# Twin Dual-Environment Bridge

This branch defines the shared contract for two Codex environments intended to behave as
functional twins.

## Contract

Both environments must use:
- repository: `fscfede-beep/verifiable-agent-control-plane`
- branch: `twin/dual-environment-bridge`
- identical TwinSpec digest
- identical tool-policy digest
- identical runtime/test baseline

## Lifecycle

`INTENT -> AUTHORITY -> PREFLIGHT -> EXECUTION -> READBACK -> FALSIFICATION -> CLOSURE`

## Equivalence gate

Promotion is allowed only when A and B agree on:
- repository commit SHA
- TwinSpec digest
- tool-policy digest
- runtime version
- required test status

A mismatch is FAIL-CLOSED.

## Security

This bridge intentionally does not store or transfer passwords, cookies, OAuth tokens,
session identifiers, recovery codes, API keys, or other authentication material.

Environment-specific identifiers remain local to the environment runtime.

## Purpose

This does not merge ChatGPT accounts. It provides a shared, auditable control plane so
two separate environments can consume the same functional specification and evidence.
