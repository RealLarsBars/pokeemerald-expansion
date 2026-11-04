# Starts the Emerald Editor in the background and opens it in an app window.
# Setup.bat copies this file to %LOCALAPPDATA%\EmeraldTools and makes the
# "Emerald Editor" desktop shortcut point at it.
#
# Keep this file ASCII only: Windows PowerShell 5.1 misreads other characters.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$ConfigPath = Join-Path $env:LOCALAPPDATA 'EmeraldTools\config.json'
$Url = 'http://localhost:8765'

# This script usually runs with no window, so problems are shown in a message box.
function Stop-Editor([string]$Message) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($Message, 'Emerald Editor') | Out-Null
    exit 1
}

# Any unexpected error also ends up in a message box instead of vanishing.
trap {
    Stop-Editor ("The Emerald Editor hit a problem. Send a screenshot of this message to Claude in your project.`n`n" +
                 $_.Exception.Message + "`n" + $_.InvocationInfo.PositionMessage)
}

# Checks 127.0.0.1 directly: "localhost" may try IPv6 first and time out,
# and the editor only listens on IPv4.
function Test-Editor {
    try {
        $request = [System.Net.WebRequest]::Create('http://127.0.0.1:8765/api/ping')
        $request.Timeout = 3000
        $request.Proxy = $null
        $response = $request.GetResponse()
        $ok = ([int]$response.StatusCode -eq 200)
        $response.Close()
        return $ok
    } catch {
        return $false
    }
}

if (-not (Test-Path $ConfigPath)) { Stop-Editor 'Setup has not been run yet. Double-click Setup.bat first.' }
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

if (-not (Test-Editor)) {
    # A small notice near the clock, so it is clear something is happening.
    Add-Type -AssemblyName System.Windows.Forms, System.Drawing
    $notice = New-Object System.Windows.Forms.NotifyIcon
    $notice.Icon = [System.Drawing.SystemIcons]::Information
    $notice.Visible = $true
    $notice.ShowBalloonTip(10000, 'Emerald Editor', 'Starting the editor, this can take a moment...', 'Info')
    # Pass the mGBA path into Ubuntu so the Play button can open it.
    $env:EMERALD_MGBA = [string]$config.mgbaPath
    $env:WSLENV = 'EMERALD_MGBA'
    # Runs in the background with no window; its messages go to a log file.
    Start-Process -FilePath 'wsl.exe' -WindowStyle Hidden -ArgumentList (
        "-d $($config.distro) --cd `"$($config.linuxProject)`" -- bash -c `"python3 editor/server.py > /tmp/emerald-editor.log 2>&1`"")

    $started = $false
    for ($i = 0; $i -lt 180; $i++) {   # up to 90 seconds
        Start-Sleep -Milliseconds 500
        if (Test-Editor) { $started = $true; break }
    }
    $notice.Dispose()
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
