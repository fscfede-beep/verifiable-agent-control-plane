#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, platform, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        return (p.stdout or p.stderr).strip()
    except Exception as e:
        return f"ERROR: {e}"

def sha256_text(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    twin = ROOT / "twin" / "environment-bridge.yaml"
    bridge = ROOT / "twin" / "ENVIRONMENT_BRIDGE.md"
    print(json.dumps({
        "repository": "fscfede-beep/verifiable-agent-control-plane",
        "branch": run(["git","branch","--show-current"]),
        "commit": run(["git","rev-parse","HEAD"]),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "twin_bridge_sha256": sha256_text(bridge) if bridge.exists() else None,
        "twin_config_sha256": sha256_text(twin) if twin.exists() else None,
        "tests": run(["python","-m","unittest","discover","-s","tests","-v"]),
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
