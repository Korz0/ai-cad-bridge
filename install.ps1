[CmdletBinding()]
param(
    [string]$Workspace = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'AI CAD Bridge'),
    [string]$Python,
    [string]$RuntimeRoot = (Join-Path $env:LOCALAPPDATA 'AI CAD Bridge'),
    [int]$InventorYear = 0,
    [switch]$SkipCodex
)
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Windows is required.' }
$repoRoot = $PSScriptRoot
$pluginSource = Join-Path $repoRoot 'plugins\ai-cad-bridge'
$version = (Get-Content -LiteralPath (Join-Path $pluginSource 'plugin.json') -Raw | ConvertFrom-Json).version
if (-not $Python) {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $Python = (& py.exe -3 -c 'import sys; print(sys.executable)' | Select-Object -Last 1)
    } elseif (Get-Command python.exe -ErrorAction SilentlyContinue) {
        $Python = (& python.exe -c 'import sys; print(sys.executable)' | Select-Object -Last 1)
    }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) { throw 'Install 64-bit Python 3.11-3.14 from python.org, then rerun; or use -Python <python.exe>.' }
& $Python -c "import sys,struct; assert (3,11) <= sys.version_info[:2] <= (3,14) and struct.calcsize('P')==8, '64-bit Python 3.11-3.14 required'"
if ($LASTEXITCODE -ne 0) { throw 'Unsupported Python interpreter.' }
if ($InventorYear -and ($InventorYear -lt 2017 -or $InventorYear -gt 2027)) { throw 'InventorYear must be 2017-2027.' }
$Workspace = [IO.Path]::GetFullPath($Workspace)
$RuntimeRoot = [IO.Path]::GetFullPath($RuntimeRoot)
New-Item -ItemType Directory -Force -Path $Workspace,$RuntimeRoot | Out-Null
$venv = Join-Path $RuntimeRoot ("runtime-" + $version)
$runtimePython = Join-Path $venv 'Scripts\python.exe'
Write-Host 'Preparing isolated Python runtime (no administrator rights required)...'
& $Python -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
& $runtimePython -m pip install --disable-pip-version-check -c (Join-Path $repoRoot 'requirements-lock.txt') $pluginSource
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check internet/PyPI access and rerun.' }
& $runtimePython -c "import cad_bridge.server, pythoncom; print('Runtime imports OK')"
if ($LASTEXITCODE -ne 0) { throw 'Runtime verification failed.' }
$configFile = Join-Path $RuntimeRoot 'config.json'
if (Test-Path -LiteralPath $configFile) { Copy-Item -LiteralPath $configFile -Destination ($configFile + '.bak') -Force }
$config = @{version=$version; python=$runtimePython; workspace=$Workspace; inventor_year=$InventorYear; repository=$repoRoot}
[IO.File]::WriteAllText($configFile,($config | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
if (-not $SkipCodex) {
    if ($RuntimeRoot -ne [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'AI CAD Bridge'))) {
        throw 'Custom RuntimeRoot requires -SkipCodex and AI_CAD_BRIDGE_CONFIG for manual MCP use.'
    }
    if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
        throw 'Runtime installed. Codex CLI is not on PATH. Add it to PATH and rerun, or use the manual MCP instructions in docs/INSTALL.md.'
    }
    & codex plugin marketplace add $repoRoot
    if ($LASTEXITCODE -ne 0) { throw 'Marketplace registration failed. Check codex plugin --help.' }
    & codex plugin add 'ai-cad-bridge@ai-cad-bridge-community'
    if ($LASTEXITCODE -ne 0) { throw 'Plugin installation failed; runtime and config were preserved.' }
}
Write-Host "Installed runtime $version. Workspace: $Workspace"
Write-Host 'Open Inventor, restart Codex, and start a new local chat with AI CAD Bridge.'
Write-Host "Configuration: $configFile"
