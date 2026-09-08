# Memory Policy

## Canonical sources

1. GitHub repository `fscfede-beep/verifiable-agent-control-plane`: canonical software, configuration, tests, and versioned evidence.
2. Stele project `rumbo-twin-cuentas-gemelas-h4sku`: canonical project state, decisions, architecture, tasks, and audit status.
3. Memco Shared Memory: secondary reusable team knowledge only.

## Rule

Never treat two memory systems as independent authorities for the same project state. If Stele and Memco disagree, Stele is authoritative for project state; investigate and record the reconciliation.

## Account boundary

Neither memory system grants access to a ChatGPT account, session, cookie, token, or provider authorization. Those remain independent per account/workspace.

## Twin acceptance

A and B are not declared functional twins until:
- both run the same repository commit;
- both use the same TwinSpec and tool policy;
- required plugin/skill versions agree;
- both test suites pass;
- A/B attestation returns PASS;
- any provider authorization differences are documented.
