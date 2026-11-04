# Starts the Emerald Editor in the background and opens it in an app window.
# Setup.bat copies this file to %LOCALAPPDATA%\EmeraldTools and makes the
# "Emerald Editor" desktop shortcut point at it.
#
# Keep this file ASCII only: Windows PowerShell 5.1 misreads other characters.

$ErrorActionPreference = 'Stop'
$ConfigPath = Join-Path $env:LOCALAPPDATA 'EmeraldTools\config.json'
$Url = 'http://localhost:8765'

# This script usually runs with no window, so problems are shown in a message box.
function Stop-Editor([string]$Message) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($Message, 'Emerald Editor') | Out-Null
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
    # Runs in the background with no window; its messages go to a log file.
    Start-Process -FilePath 'wsl.exe' -WindowStyle Hidden -ArgumentList (
        "-d $($config.distro) --cd `"$($config.linuxProject)`" -- bash -c `"python3 editor/server.py > /tmp/emerald-editor.log 2>&1`"")

    $started = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-Editor) { $started = $true; break }
    }
    if (-not $started) {
        $log = (& wsl.exe -d $config.distro -- tail -n 15 /tmp/emerald-editor.log 2>$null) -join "`n"
        Stop-Editor ("The editor did not start. Send a screenshot of this message to Claude in your project.`n`n" + $log)
    }
}

# Open it as its own app window (no tabs or address bar) with Edge or Chrome,
# or in the default browser if neither is found.
$opened = $false
foreach ($browser in @('msedge.exe', 'chrome.exe')) {
    try {
        Start-Process -FilePath $browser -ArgumentList "--app=$Url" -ErrorAction Stop
        $opened = $true
        break
    } catch { }
}
if (-not $opened) { Start-Process $Url }
