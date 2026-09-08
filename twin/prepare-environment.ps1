param(
  [ValidateSet("primary","twin")][string]$Role,
  [Parameter(Mandatory=$true)][string]$EnvironmentId,
  [string]$RepoUrl = "https://github.com/fscfede-beep/verifiable-agent-control-plane.git",
  [string]$Branch = "main",
  [string]$Target = "$HOME\twin-verifiable-agent-control-plane"
)

$ErrorActionPreference = "Stop"

if (-not $Role) { throw "Indica -Role primary o twin." }
if ($EnvironmentId -match '[\\/:*?"<>|\s]') { throw "EnvironmentId inválido." }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git no está instalado o no está en PATH."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python no está instalado o no está en PATH."
}

if (Test-Path $Target) {
  git -C $Target fetch origin
  git -C $Target checkout $Branch
  git -C $Target reset --hard "origin/$Branch"
} else {
  git clone --branch $Branch $RepoUrl $Target
}

Set-Location $Target

$env:TWIN_ENV_ROLE = $Role
$env:TWIN_ENV_ID = $EnvironmentId

python -m pip install .
python -m unittest discover -s tests -v
python twin/twin-doctor.py | Tee-Object -FilePath "$Target\$EnvironmentId.twin-doctor.json"

Write-Host ""
Write-Host "TWIN ENVIRONMENT READY" -ForegroundColor Green
Write-Host "Role: $Role"
Write-Host "ID:   $EnvironmentId"
Write-Host "Repo: $Target"
Write-Host "Attestation: $Target\$EnvironmentId.twin-doctor.json"
Write-Host ""
Write-Host "No se copiaron ni almacenaron credenciales, cookies o sesiones."
