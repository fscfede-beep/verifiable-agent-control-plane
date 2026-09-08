param(
  [ValidateSet("primary","twin")][string]$Role,
  [Parameter(Mandatory=$true)][string]$EnvironmentId,
  [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference="Stop"
python -m unittest discover -s tests -v
$testCode=$LASTEXITCODE
if ($testCode -ne 0) {
  Write-Error "FAIL-CLOSED: test suite failed with exit code $testCode"
  exit $testCode
}
python twin/collect_attestation.py --role $Role --id $EnvironmentId --out $Output --tests-result PASS
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
