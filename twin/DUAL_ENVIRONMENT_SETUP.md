# Dual-environment twin setup

Use the same repository and branch in both Codex environments.

## 1. Shared source

Repository:
https://github.com/fscfede-beep/verifiable-agent-control-plane

Branch:
twin/dual-environment-bridge

## 2. Two Codex environments

Create Environment A and Environment B in the Codex UI under Settings > Environments.
Point both environments at the same repository and branch.

The environment identifiers are intentionally NOT stored in GitHub.

## 3. Own plugins

This branch contains two plugin packages:

- Twin Control Plane
- Twin Sync

and a Codex marketplace manifest at:
`.agents/plugins/marketplace.json`

A local/Codex-specific plugin may need to be imported or made available by the applicable
workspace/admin controls before it can be used.

## 4. Workspace marketplace (only where applicable)

OpenAI currently documents GitHub marketplace import under **Workspace settings > Plugins**
for eligible workspace administrators. This is a workspace-admin feature; it is not a
general mechanism for merging two personal ChatGPT accounts.

A synced marketplace updates plugin content, but it does not transfer account identity,
provider credentials, OAuth authorization, cookies, sessions, or repository permissions.

## 5. App authorization

If a plugin includes an app, each account/workspace must satisfy that app's own availability,
provider authorization, role access, action controls and approval requirements.

## 6. Equivalence gate

Both environments must report:

- repository commit SHA;
- TwinSpec digest;
- tool-policy digest;
- runtime baseline;
- test status;
- installed Twin plugin versions.

Any required mismatch is FAIL-CLOSED.

## 7. Security

Never commit:
- passwords
- cookies
- OAuth/access tokens
- API keys
- recovery codes
- session identifiers

## 8. Verification command

Run from each environment:

```bash
python twin/twin-doctor.py
python -m unittest discover -s tests -v
```

Compare the outputs. Identical required evidence is the acceptance condition for a
functional twin.