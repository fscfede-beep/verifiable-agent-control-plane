param(
  [ValidateSet("primary","twin")][string]$Role,
  [Parameter(Mandatory=$true)][string]$EnvironmentId,
  [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference="Stop"

# The collector owns test execution. It writes an attestation only after the real suite passes.
python twin/collect_attestation.py --role $Role --id $EnvironmentId --out $Output
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
