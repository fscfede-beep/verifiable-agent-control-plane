param(
  [ValidateSet("primary","twin")][string]$Role,
  [Parameter(Mandatory=$true)][string]$EnvironmentId,
  [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference="Stop"

python twin/collect_attestation.py --role $Role --id $EnvironmentId --out $Output
if ($LASTEXITCODE -ne 0) {
  Write-Error "FAIL-CLOSED: test suite failed or attestation collection failed with exit code $LASTEXITCODE"
  exit $LASTEXITCODE
}
