# Read-only browser probe

The screenshot supplied in the project shows a Chromium-family browser with ChatGPT/Codex tabs.
OpenAI currently documents Browser Use, the in-app browser, and developer-mode CDP for supported
Codex experiences. The built-in browser is separate from the user's normal Chrome profile; when
an existing signed-in profile is required, OpenAI documents using the Codex Chrome extension.

This project also provides an independent, read-only CDP probe for local diagnostics.

## What it does

- Connects only to localhost CDP.
- Reads page URL, title and a bounded visible-text sample.
- Does not navigate, click, submit, write files on the target site, or read cookies/storage.
- Produces JSON suitable for comparing two environments.

## Example

Start your Chromium-family browser with a localhost DevTools endpoint of your choosing,
then run:

```bash
python -m pip install websocket-client
python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:9222 --out browser_probe.json
```

Do not expose the debugging port to the network.

## Interpretation

The probe can identify which ChatGPT/Codex pages are open and collect visible configuration
text. It cannot establish that two accounts are fused; it is evidence for the functional-twin
inventory only.
