param(
  [string]$RepoUrl = "https://github.com/fscfede-beep/verifiable-agent-control-plane.git",
  [string]$Branch = "main",
  [string]$Target = "$HOME\\twin-verifiable-agent-control-plane"
)

$ErrorActionPreference = "Stop"
Write-Host "== RUMBO Twin Bootstrap =="
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git no está instalado o no está en PATH." }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python no está instalado o no está en PATH." }

if (Test-Path $Target) {
  git -C $Target fetch origin
  git -C $Target checkout $Branch
  git -C $Target reset --hard "origin/$Branch"
} else {
  git clone --branch $Branch $RepoUrl $Target
}

Set-Location $Target
Write-Host "== Verificación Git =="
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
Write-Host "== Instalación =="
python -m pip install .
Write-Host "== Tests =="
python -m unittest discover -s tests -v
Write-Host "== Twin Doctor =="
python twin/twin-doctor.py
Write-Host "== OK =="
Write-Host "Este entorno ya usa el contrato TWIN compartido."
Write-Host "No se copian contraseñas, cookies, tokens ni sesiones."
Write-Host "Ejecute el mismo script en el segundo entorno para comparar las huellas."
