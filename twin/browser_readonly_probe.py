#!/usr/bin/env python3
"""
Read-only Chromium CDP probe for Twin environment discovery.

Security boundary:
- Connects only to a localhost CDP endpoint.
- Reads page metadata and bounded visible body text.
- Never reads cookies, browser storage, authentication headers, or tokens.
- Does not click, navigate, submit forms, or mutate pages.
- Intended to inventory already-open ChatGPT/Codex tabs so A/B can be compared.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
import websocket

def get_targets(endpoint: str):
    url = endpoint.rstrip("/") + "/json/list"
    with urllib.request.urlopen(url, timeout=3) as r:
        return json.load(r)

def cdp_eval(ws, expression: str):
    cdp_eval.counter += 1
    ws.send(json.dumps({
        "id": cdp_eval.counter,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        },
    }))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == cdp_eval.counter:
            return msg.get("result", {}).get("result", {}).get("value")
cdp_eval.counter = 0

def probe_target(target):
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=3)
    try:
        title = cdp_eval(ws, "document.title")
        url = cdp_eval(ws, "location.href")
        text = cdp_eval(ws, "document.body ? document.body.innerText.slice(0, 12000) : ''")
        return {
            "title": title,
            "url": url,
            "visible_text_sample": text,
        }
    finally:
        ws.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", default="http://127.0.0.1:9222")
    p.add_argument("--out", default="browser_probe.json")
    args = p.parse_args()

    targets = get_targets(args.endpoint)
    results = []
    for t in targets:
        if t.get("type") != "page" or "webSocketDebuggerUrl" not in t:
            continue
        try:
            results.append(probe_target(t))
        except Exception as e:
            results.append({"title": t.get("title"), "url": t.get("url"), "error": str(e)})

    report = {
        "mode": "READ_ONLY",
        "endpoint": args.endpoint,
        "targets": results,
        "security": {
            "cookies_read": False,
            "storage_read": False,
            "navigation": False,
            "clicks": False,
            "form_submission": False,
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
