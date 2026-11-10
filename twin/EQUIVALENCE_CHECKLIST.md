# Twin equivalence checklist

Run this checklist independently in Environment A and Environment B.

## Identity boundary
- [ ] Different ChatGPT account identities remain separate.
- [ ] No session cookies, OAuth tokens, API keys, passwords or recovery codes are copied.

## Shared state
- [ ] Repository = `fscfede-beep/verifiable-agent-control-plane`
- [ ] Branch = `twin/dual-environment-bridge`
- [ ] Commit SHA matches.
- [ ] `TwinSpec` digest matches.
- [ ] Tool-policy digest matches.
- [ ] Runtime baseline matches.
- [ ] Tests pass.

## Plugins
- [ ] Same Twin Control Plane plugin version.
- [ ] Same Twin Sync plugin version.
- [ ] Same required app set.
- [ ] Same app action/approval policy.
- [ ] Each external provider connection is authorized independently.

## Verification
- [ ] Run `python twin/twin-doctor.py` in both environments.
- [ ] Compare the JSON outputs.
- [ ] Any required mismatch is FAIL-CLOSED.
- [ ] Only after this gate passes should a shared change be promoted.

## Important
A synchronized GitHub marketplace synchronizes plugin content; it does not grant provider
permissions or connect accounts automatically. Those authorizations remain local to each
account/workspace.
