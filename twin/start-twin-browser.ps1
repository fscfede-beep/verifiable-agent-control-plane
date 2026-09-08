param(
  [int]$PortA = 9222,
  [int]$PortB = 9223,
  [string]$Repo = "https://github.com/fscfede-beep/verifiable-agent-control-plane",
  [string]$CodexUrl = "https://chatgpt.com/codex"
)
$ErrorActionPreference = "Stop"

function Find-Browser {
  $candidates = @(
    "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  throw "No se encontró Brave ni Chrome en rutas estándar."
}

function Start-TwinBrowser($exe, $name, $port) {
  $profile = Join-Path $HOME "RUMBO-Twin-$name"
  New-Item -ItemType Directory -Force -Path $profile | Out-Null
  $args = @(
    "--remote-debugging-port=$port",
    "--user-data-dir=$profile",
    "--no-first-run",
    "--no-default-browser-check",
    $CodexUrl
  )
  Start-Process -FilePath $exe -ArgumentList $args
  Write-Host "$name iniciado en http://127.0.0.1:$port" -ForegroundColor Green
  Write-Host "Inicia sesión manualmente con la cuenta correspondiente a $name."
}

$exe = Find-Browser
Write-Host "Navegador: $exe"
Start-TwinBrowser $exe "A" $PortA
Start-TwinBrowser $exe "B" $PortB

Write-Host ""
Write-Host "== RUMBO Twin =="
Write-Host "A: puerto $PortA / perfil RUMBO-Twin-A"
Write-Host "B: puerto $PortB / perfil RUMBO-Twin-B"
Write-Host ""
Write-Host "Después de iniciar sesión en ambos perfiles, ejecutá:"
Write-Host "python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:$PortA --out A.browser.json"
Write-Host "python twin/browser_readonly_probe.py --endpoint http://127.0.0.1:$PortB --out B.browser.json"
Write-Host ""
Write-Host "No copies cookies, tokens, passwords ni perfiles entre A y B." -ForegroundColor Yellow
