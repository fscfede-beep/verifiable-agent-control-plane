# Dual-environment twin setup

Use the same repository and branch in both Codex environments.

## 1. Clone / open the same source

Repository:
https://github.com/fscfede-beep/verifiable-agent-control-plane

Branch:
twin/dual-environment-bridge

## 2. Register the same marketplace

Codex CLI:

```bash
codex plugin marketplace add fscfede-beep/verifiable-agent-control-plane --ref twin/dual-environment-bridge
codex plugin marketplace list
```

The repository contains:
`./.agents/plugins/marketplace.json`

## 3. Install the same twin plugins

In the ChatGPT desktop Plugins Directory, select the `RUMBO Twin Plugins` marketplace and install:
- Twin Control Plane
- Twin Sync

Equivalent local policy is AVAILABLE / authentication ON_INSTALL.

## 4. Run the equivalence gate

Both environments must use:
- the same commit SHA;
- the same TwinSpec;
- the same tool policy;
- the same runtime baseline;
- the same tests.

Any mismatch is FAIL-CLOSED.

## 5. Important account boundary

This creates a shared plugin/workflow source. It does NOT transfer provider credentials,
account sessions, cookies, OAuth tokens, or repository permissions.

Each ChatGPT/Codex account must authorize the apps it uses with its own account.

## 6. Workspace marketplace option

For a managed workspace where you are an admin, OpenAI also supports importing
`.agents/plugins/marketplace.json` from a GitHub repository in Workspace settings > Plugins.
That mechanism synchronizes plugin content but still does not connect member accounts or
grant app permissions automatically.
