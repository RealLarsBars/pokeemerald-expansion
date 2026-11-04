# Builds whatever changed in the Emerald project and opens the game in mGBA.
# Setup.bat copies this file to %LOCALAPPDATA%\EmeraldTools and makes the
# "Play Emerald" desktop shortcut point at it.
#
# Keep this file ASCII only: Windows PowerShell 5.1 misreads other characters.

$ErrorActionPreference = 'Stop'
$ConfigPath = Join-Path $env:LOCALAPPDATA 'EmeraldTools\config.json'

function Stop-Play([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Press Enter to close this window'
    exit 1
}

if (-not (Test-Path $ConfigPath)) { Stop-Play 'Setup has not been run yet. Double-click Setup.bat first.' }
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

Write-Host 'Building your changes...' -ForegroundColor Cyan
$script = "cd '$($config.linuxProject)' && make -j`$(nproc)`n"
$script | & wsl.exe -d $config.distro -- bash -s
if ($LASTEXITCODE -ne 0) {
    Stop-Play 'The build failed, so the game was not started. Scroll up to see the error, and send it to Claude in your project.'
}

$mgba = $config.mgbaPath
if (-not $mgba -or -not (Test-Path $mgba)) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Find mGBA.exe'
    $dialog.Filter = 'mGBA (mGBA.exe)|mGBA.exe|Programs (*.exe)|*.exe'
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        Stop-Play "The game was built but mGBA was not picked. The game file is at $($config.rom)"
    }
    $mgba = $dialog.FileName
    $config.mgbaPath = $mgba
    $config | ConvertTo-Json | Set-Content -Path $ConfigPath -Encoding UTF8
}

Write-Host 'Starting the game.' -ForegroundColor Green
Start-Process -FilePath $mgba -ArgumentList "`"$($config.rom)`""
