# Environment A/B bootstrap

## Environment A
Create a Codex Cloud environment from:
- repository: fscfede-beep/verifiable-agent-control-plane
- branch: main

## Environment B
Create a second Codex Cloud environment from the same repository and branch.

## Shared runtime contract
The repository root contains AGENTS.md. Codex uses that project guidance to apply the same
behavioral and verification rules in both environments.

## First-run verification

In each environment run:

```bash
python twin/twin-doctor.py
python -m unittest discover -s tests -v
```

Then compare:
- git commit
- TwinSpec/tool-policy hashes
- runtime
- test results

## Important
Creating two environments does not merge the underlying ChatGPT accounts. Each environment
retains its own account/workspace authentication and external app authorization.
