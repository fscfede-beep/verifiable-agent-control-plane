# RUMBO Twin Operator Runbook

## Goal

Run two independent ChatGPT/Codex accounts as a functional twin using one versioned source
of truth. Do not attempt to merge account identities or copy sessions.

## Reality check

Personal ChatGPT accounts remain separate. OpenAI documents GitHub marketplace synchronization
as a workspace-admin capability. Plugins can package skills/apps, but provider authorization
remains account/workspace-specific.

Therefore the reliable common layer for two accounts is:
1. shared Git repository;
2. shared AGENTS.md;
3. shared skills/plugins where permitted;
4. shared TwinSpec and tool policy;
5. independent provider authorizations;
6. A/B attestation.

## Environment A / B

Create two Codex environments pointing to:

Repository:
https://github.com/fscfede-beep/verifiable-agent-control-plane

Branch:
main

Environment A:
TWIN_ENV_ROLE=primary
TWIN_ENV_ID=<unique local identifier>

Environment B:
TWIN_ENV_ROLE=twin
TWIN_ENV_ID=<unique local identifier>

Never commit account/session details to GitHub.

## First run

From repository root:

```bash
python -m pip install .
python -m unittest discover -s tests -v
python twin/twin-doctor.py
```

Save the JSON output of each environment locally.

## Attestation

Compare the outputs:

```bash
python twin/attestation-gate.py A.json B.json
```

A required mismatch returns FAIL-CLOSED.

## Browser evidence

The repository also contains a read-only local Chromium CDP probe for already-open pages:

```bash
python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:9222
```

Only use a localhost debugging endpoint you intentionally enabled. Keep the endpoint off
the network. The probe is designed not to navigate, click, submit forms, or read browser
cookies/storage.

## What is shared

- code;
- AGENTS.md;
- TwinSpec;
- plugin/skill source;
- tool policy;
- tests;
- audit logic;
- evidence classification.

## What is deliberately not shared

- passwords;
- cookies;
- session identifiers;
- OAuth/access tokens;
- API keys;
- recovery codes;
- provider account sessions;
- subscription entitlements.

## Acceptance condition

The environments are a functional twin only when:
- the same repository commit is used;
- the same TwinSpec/tool policy is used;
- required plugin/skill versions agree;
- tests pass;
- authorization differences are documented;
- the A/B attestation gate returns PASS.

A visual impression that two browser sessions look identical is not sufficient evidence.
