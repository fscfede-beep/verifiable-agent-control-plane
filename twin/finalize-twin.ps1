param(
  [Parameter(Mandatory=$true)][string]$A,
  [Parameter(Mandatory=$true)][string]$B
)
$ErrorActionPreference="Stop"

if (-not (Test-Path $A -PathType Leaf)) { throw "A attestation not found: $A" }
if (-not (Test-Path $B -PathType Leaf)) { throw "B attestation not found: $B" }

python twin/attestation-gate.py $A $B
if ($LASTEXITCODE -eq 0) {
  Write-Host "RUMBO TWIN FINAL RESULT: PASS" -ForegroundColor Green
  exit 0
}
Write-Host "RUMBO TWIN FINAL RESULT: FAIL-CLOSED" -ForegroundColor Red
exit $LASTEXITCODE
