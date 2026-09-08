param([int]$PortA=9222,[int]$PortB=9223)
$ErrorActionPreference="Stop"
python twin/browser_readonly_probe.py --endpoint "http://127.0.0.1:$PortA" --out A.browser.json
python twin/browser_readonly_probe.py --endpoint "http://127.0.0.1:$PortB" --out B.browser.json
python twin/browser_attestation_gate.py A.browser.json B.browser.json
