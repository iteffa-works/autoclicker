# Збірка dist\autoclicker.exe. Завершує запущений autoclicker.exe, інакше PyInstaller не може перезаписати файл (WinError 5).
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$proc = Get-Process -Name "autoclicker" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Зупинка запущеного autoclicker.exe..."
    $proc | Stop-Process -Force
    Start-Sleep -Seconds 1
}

python -m PyInstaller --clean --noconfirm autoclicker.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Готово: $projectRoot\dist\autoclicker.exe"
