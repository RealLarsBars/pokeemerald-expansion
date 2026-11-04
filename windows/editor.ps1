# Starts the Emerald Editor and opens it in an app window.
# Setup.bat copies this file to %LOCALAPPDATA%\EmeraldTools and makes the
# "Emerald Editor" desktop shortcut point at it.
#
# Keep this file ASCII only: Windows PowerShell 5.1 misreads other characters.

$ErrorActionPreference = 'Stop'
$ConfigPath = Join-Path $env:LOCALAPPDATA 'EmeraldTools\config.json'
$Url = 'http://localhost:8765'

function Stop-Editor([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Press Enter to close this window'
    exit 1
}

function Test-Editor {
    try {
        $r = Invoke-WebRequest -Uri "$Url/api/ping" -UseBasicParsing -TimeoutSec 2
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

if (-not (Test-Path $ConfigPath)) { Stop-Editor 'Setup has not been run yet. Double-click Setup.bat first.' }
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

if (-not (Test-Editor)) {
    Write-Host 'Starting the Emerald Editor...' -ForegroundColor Cyan
    # Pass the mGBA path into Ubuntu so the Play button can open it.
    $env:EMERALD_MGBA = [string]$config.mgbaPath
    $env:WSLENV = 'EMERALD_MGBA'
    Start-Process -FilePath 'wsl.exe' -WindowStyle Minimized -ArgumentList @(
        '-d', $config.distro, '--cd', $config.linuxProject, '--', 'python3', 'editor/server.py')

    $started = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-Editor) { $started = $true; break }
    }
    if (-not $started) {
        Stop-Editor ("The editor did not start. Open the minimized 'wsl' window on your taskbar to see why, " +
                     "and send a screenshot of it to Claude in your project.")
    }
}

# Open it like an app (no address bar) in Edge, or in the default browser.
try {
    Start-Process -FilePath 'msedge.exe' -ArgumentList "--app=$Url"
} catch {
    Start-Process $Url
}
