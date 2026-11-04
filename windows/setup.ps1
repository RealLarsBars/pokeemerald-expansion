# One-time setup for editing and playing this Pokemon Emerald project on Windows.
#
# What it does (it is safe to run again; finished steps are skipped):
#   1. Installs WSL with Ubuntu (asks for admin rights, may need one restart).
#   2. Installs the build tools inside Ubuntu.
#   3. Downloads the project into a folder called "Emerald" inside Ubuntu.
#   4. Builds the game once to check everything works.
#   5. Finds mGBA and puts "Emerald Editor", "Emerald Project" and "Play Emerald"
#      shortcuts on the desktop.
#
# Keep this file ASCII only: Windows PowerShell 5.1 misreads other characters.

$ErrorActionPreference = 'Stop'

$Distro      = 'Ubuntu'
$RepoUrl     = 'https://github.com/RealLarsBars/pokeemerald-expansion.git'
$FolderName  = 'Emerald'
$ToolsDir    = Join-Path $env:LOCALAPPDATA 'EmeraldTools'
$ConfigPath  = Join-Path $ToolsDir 'config.json'
$RunOnceKey  = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce'
$Packages    = 'build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi git libpng-dev python3'

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Stop-Setup([string]$Message) {
    Write-Host ''
    Write-Host $Message -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Press Enter to close this window'
    exit 1
}

# Runs a bash script inside Ubuntu. The script is sent through stdin so that
# no Windows quoting rules get in the way. Output goes straight to the window;
# the only thing returned is bash's exit code.
function Invoke-Wsl([string]$Script, [switch]$AsRoot) {
    # PowerShell adds a Windows line ending (CR LF) after piped text. End the
    # script with a comment line so that stray CR is ignored by bash.
    $body = ($Script -replace "`r", '') + "`n# end"
    if ($AsRoot) {
        $body | & wsl.exe -d $Distro -u root -- bash -s | Out-Host
    } else {
        $body | & wsl.exe -d $Distro -- bash -s | Out-Host
    }
    return $LASTEXITCODE
}

function Test-Distro {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return $false }
    try {
        & wsl.exe -d $Distro -u root -- true 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Register-ResumeAfterRestart {
    $command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    New-Item -Path $RunOnceKey -Force | Out-Null
    Set-ItemProperty -Path $RunOnceKey -Name 'EmeraldSetup' -Value $command
}

function Find-Mgba {
    $candidates = @(
        (Join-Path $env:ProgramFiles 'mGBA\mGBA.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'mGBA\mGBA.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\mGBA\mGBA.exe'),
        (Join-Path $env:USERPROFILE 'scoop\apps\mgba\current\mGBA.exe')
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    $cmd = Get-Command mGBA.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    Write-Host 'I could not find mGBA. A window will open: please pick mGBA.exe.' -ForegroundColor Yellow
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Find mGBA.exe'
    $dialog.Filter = 'mGBA (mGBA.exe)|mGBA.exe|Programs (*.exe)|*.exe'
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.FileName }
    return ''
}

function New-Shortcut([string]$Name, [string]$Target, [string]$Arguments, [string]$Icon) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut((Join-Path $desktop "$Name.lnk"))
    $link.TargetPath = $Target
    if ($Arguments) { $link.Arguments = $Arguments }
    if ($Icon) { $link.IconLocation = $Icon }
    $link.Save()
}

Write-Host 'Pokemon Emerald project setup' -ForegroundColor Green
Write-Host 'This can take a while the first time. Leave this window open until it says it is finished.'

# 1. WSL + Ubuntu ------------------------------------------------------------
Write-Step 'Checking for Ubuntu (WSL)'
if (-not (Test-Distro)) {
    $ubuntuExe = Get-Command ubuntu.exe -ErrorAction SilentlyContinue
    if ($ubuntuExe) {
        # Ubuntu is installed from the Store but was never opened. Finish its
        # install without asking for a Linux username and password.
        Write-Host 'Finishing the Ubuntu install...'
        & $ubuntuExe.Source install --root | Out-Host
    } else {
        Write-Host 'Installing WSL and Ubuntu. Windows will ask for permission: click Yes.'
        try {
            $proc = Start-Process -FilePath 'wsl.exe' -ArgumentList '--install', '-d', $Distro, '--no-launch' -Verb RunAs -Wait -PassThru
        } catch {
            Stop-Setup 'The WSL install was cancelled. Run Setup.bat again and click Yes when Windows asks.'
        }
        if ($proc.ExitCode -ne 0) {
            Stop-Setup ("The WSL install failed (code $($proc.ExitCode)). The most common cause is that " +
                        "virtualization is turned off in your PC's BIOS. Search the web for your PC model " +
                        "plus 'enable virtualization', turn it on, then run Setup.bat again.")
        }
        $ubuntuExe = Get-Command ubuntu.exe -ErrorAction SilentlyContinue
        if (-not (Test-Distro) -and $ubuntuExe) {
            & $ubuntuExe.Source install --root | Out-Host
        }
    }

    if (-not (Test-Distro)) {
        Register-ResumeAfterRestart
        Stop-Setup ("WSL is installed but Windows needs a restart. Restart your PC now. " +
                    "Setup will continue by itself after you log back in.`n`n" +
                    "If it does not continue, open 'Ubuntu' from the Start menu once, " +
                    "choose any username and password, close it, then run Setup.bat again.")
    }
}
Write-Host 'Ubuntu is ready.'

# 2. Build tools -------------------------------------------------------------
Write-Step 'Installing the build tools (this is the slow part)'
$code = Invoke-Wsl -AsRoot @"
set -e
export DEBIAN_FRONTEND=noninteractive
if dpkg -s $Packages >/dev/null 2>&1; then
    echo 'Build tools are already installed.'
else
    APT='-y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold'
    apt-get update
    # On WSL 1, systemd's update script cannot lock /etc/passwd and fails, which
    # leaves apt stuck. Nothing uses systemd-sysusers there, so make it a no-op.
    if grep -q Microsoft /proc/version && [ ! -e /usr/bin/systemd-sysusers.distrib ]; then
        echo 'WSL 1 detected: working around the systemd-sysusers update problem.'
        dpkg-divert --local --rename --add /usr/bin/systemd-sysusers
        ln -sf /bin/true /usr/bin/systemd-sysusers
    fi
    # Repair a half-finished Ubuntu update first, or apt refuses to install anything.
    # This can still report errors (for example a library that needs updating);
    # the --fix-broken step below sorts those out, so do not stop here.
    dpkg --configure -a || true
    apt-get `$APT --fix-broken install
    apt-get `$APT full-upgrade
    apt-get `$APT install $Packages
fi
"@
if ($code -ne 0) { Stop-Setup 'Installing the build tools failed. Check your internet connection and run Setup.bat again.' }

# 3. Project folder ----------------------------------------------------------
Write-Step "Downloading the project into the '$FolderName' folder"
$linuxHome = (('echo $HOME' + "`n# end") | & wsl.exe -d $Distro -- bash -s | Select-Object -Last 1).Trim()
if (-not $linuxHome) { Stop-Setup 'Could not find your Ubuntu home folder.' }
$linuxProject = "$linuxHome/$FolderName"

$code = Invoke-Wsl @"
set -e
if [ -d '$linuxProject/.git' ]; then
    echo 'The project folder already exists, keeping your changes.'
    cd '$linuxProject'
    if [ -z "`$(git status --porcelain)" ]; then
        git pull --ff-only || echo 'Could not fetch the newest version right now; carrying on.'
    else
        echo 'You have edits in progress, so I did not fetch updates. Use the Update button in the editor.'
    fi
else
    git clone '$RepoUrl' '$linuxProject'
fi
"@
if ($code -ne 0) { Stop-Setup 'Downloading the project failed. Check your internet connection and run Setup.bat again.' }

$uncRoot = "\\wsl.localhost\$Distro"
if (-not (Test-Path "$uncRoot\")) { $uncRoot = "\\wsl$\$Distro" }
$windowsProject = $uncRoot + ($linuxProject -replace '/', '\')

# 4. First build -------------------------------------------------------------
Write-Step 'Building the game for the first time (about 5 to 15 minutes)'
$code = Invoke-Wsl @"
cd '$linuxProject' && make -j`$(nproc)
"@
if ($code -ne 0) { Stop-Setup 'The build failed. Scroll up to see the error, and send it to Claude in your project.' }

# 5. mGBA, config and shortcuts ----------------------------------------------
Write-Step 'Finding mGBA'
$existing = $null
if (Test-Path $ConfigPath) { $existing = Get-Content $ConfigPath -Raw | ConvertFrom-Json }
if ($existing -and $existing.mgbaPath -and (Test-Path $existing.mgbaPath)) {
    $mgba = $existing.mgbaPath
} else {
    $mgba = Find-Mgba
}
if ($mgba) { Write-Host "Using $mgba" } else { Write-Host 'No mGBA picked. Play Emerald will ask for it later.' }

Write-Step 'Saving settings and making desktop shortcuts'
New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot 'play.ps1') -Destination $ToolsDir -Force
Copy-Item -Path (Join-Path $PSScriptRoot 'editor.ps1') -Destination $ToolsDir -Force

[ordered]@{
    distro        = $Distro
    linuxProject  = $linuxProject
    projectFolder = $windowsProject
    rom           = "$windowsProject\pokeemerald.gba"
    mgbaPath      = $mgba
} | ConvertTo-Json | Set-Content -Path $ConfigPath -Encoding UTF8

# A small EmeraldEditor.exe that starts the editor with no console window.
$editorExe = Join-Path $ToolsDir 'EmeraldEditor.exe'
$launcherSource = @'
using System.Diagnostics;
using System.IO;
using System.Reflection;
static class EmeraldEditorLauncher {
    static void Main() {
        string dir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        ProcessStartInfo psi = new ProcessStartInfo("powershell.exe",
            "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + Path.Combine(dir, "editor.ps1") + "\"");
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        Process.Start(psi);
    }
}
'@
try {
    Remove-Item $editorExe -Force -ErrorAction SilentlyContinue
    Add-Type -TypeDefinition $launcherSource -OutputAssembly $editorExe -OutputType WindowsApplication
} catch {
    Write-Host "Could not make EmeraldEditor.exe ($($_.Exception.Message)). The shortcut will use PowerShell instead."
}
if (Test-Path $editorExe) {
    New-Shortcut -Name 'Emerald Editor' -Target $editorExe -Icon "$env:SystemRoot\System32\shell32.dll,269"
} else {
    New-Shortcut -Name 'Emerald Editor' -Target "$PSHOME\powershell.exe" `
        -Arguments "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ToolsDir\editor.ps1`"" `
        -Icon "$env:SystemRoot\System32\shell32.dll,269"
}
New-Shortcut -Name 'Emerald Project' -Target $windowsProject -Icon "$env:SystemRoot\System32\shell32.dll,3"
$playIcon = if ($mgba) { "$mgba,0" } else { "$env:SystemRoot\System32\shell32.dll,137" }
New-Shortcut -Name 'Play Emerald' -Target "$PSHOME\powershell.exe" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$ToolsDir\play.ps1`"" -Icon $playIcon

Remove-ItemProperty -Path $RunOnceKey -Name 'EmeraldSetup' -ErrorAction SilentlyContinue

Write-Host ''
Write-Host 'All done!' -ForegroundColor Green
Write-Host "Your game folder is: $windowsProject"
Write-Host "On your desktop:"
Write-Host "  'Emerald Editor'  edits trainers, dialogue and scripts (it has its own Play button)."
Write-Host "  'Emerald Project' opens the game folder."
Write-Host "  'Play Emerald'    builds your changes and starts the game in mGBA."
Write-Host ''
Read-Host 'Press Enter to close this window'
