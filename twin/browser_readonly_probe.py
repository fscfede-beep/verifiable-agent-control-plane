#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
import websocket

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

def get_targets(endpoint: str):
    with urllib.request.urlopen(endpoint.rstrip("/") + "/json/list", timeout=3) as r:
        return json.load(r)

def cdp_eval(ws, expression: str):
    cdp_eval.counter += 1
    ws.send(json.dumps({
        "id": cdp_eval.counter,
        "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True, "awaitPromise": True},
    }))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == cdp_eval.counter:
            return msg.get("result", {}).get("result", {}).get("value")
cdp_eval.counter = 0

def safe_visible_text(text: str) -> str:
    return EMAIL_RE.sub("[REDACTED_EMAIL]", text or "")

def probe_target(target):
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=3)
    try:
        title = cdp_eval(ws, "document.title") or ""
        url = cdp_eval(ws, "location.href") or ""
        body = cdp_eval(ws, "document.body ? document.body.innerText.slice(0,12000) : ''") or ""
        parsed = urllib.parse.urlparse(url)
        return {
            "title": title,
            "scheme": parsed.scheme,
            "host": parsed.netloc,
            "path": parsed.path,
            "visible_text_sample": safe_visible_text(body),
        }
    finally:
        ws.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", default="http://127.0.0.1:9222")
    p.add_argument("--out", default="browser_probe.json")
    args = p.parse_args()

    results = []
    for target in get_targets(args.endpoint):
        if target.get("type") != "page" or "webSocketDebuggerUrl" not in target:
            continue
        try:
            results.append(probe_target(target))
        except Exception as exc:
            results.append({"title": target.get("title"), "error": str(exc)})

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
            "email_addresses_redacted": True,
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
