# RUMBO Twin Browser Harness

This harness creates two isolated Chromium-family browser profiles for the two ChatGPT/Codex
accounts. It does not copy or merge browser state.

## Why

A normal browser session is not a reliable synchronization boundary for two accounts.
Separate browser profiles give Environment A and Environment B their own login/session boundary
while both open the same Codex entrypoint.

## Launch

Open PowerShell and run:

```powershell
.\twin\start-twin-browser.ps1
```

The script starts two local browser debugging endpoints:
- A: 127.0.0.1:9222
- B: 127.0.0.1:9223

It uses two local profiles:
- `%USERPROFILE%\RUMBO-Twin-A`
- `%USERPROFILE%\RUMBO-Twin-B`

Log into each account manually in its corresponding window.

## Verify

After login:

```bash
python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:9222 --out A.browser.json
python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:9223 --out B.browser.json
python twin/attestation-gate.py A.browser.json B.browser.json
```

The read-only probe is evidence collection only. It does not read browser cookies or storage and
does not navigate or submit forms.

## Security

Keep the debugging ports on localhost. Do not expose them to the LAN or internet.
Never copy profile directories between A and B.

This creates separate browser/account sessions; it does not merge ChatGPT accounts.
