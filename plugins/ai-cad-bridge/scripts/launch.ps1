$ErrorActionPreference = 'Stop'
try {
    $configFile = $env:AI_CAD_BRIDGE_CONFIG
    if (-not $configFile) { $configFile = Join-Path $env:LOCALAPPDATA 'AI CAD Bridge\config.json' }
    if (-not (Test-Path -LiteralPath $configFile)) { throw 'AI CAD Bridge is not configured. Run install.ps1 from the downloaded repository.' }
    $cfg = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
    $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\plugin.json') -Raw | ConvertFrom-Json
    if ($cfg.version -ne $manifest.version) { throw 'Plugin/runtime version mismatch. Run install.ps1 from the matching release.' }
    if (-not (Test-Path -LiteralPath $cfg.python)) { throw 'Python runtime missing. Run install.ps1 again.' }
    $env:AI_CAD_WORKSPACE = $cfg.workspace
    $env:PYTHONUTF8 = '1'
    $env:PYTHONUNBUFFERED = '1'
    if ($cfg.inventor_year) { $env:AI_CAD_INVENTOR_YEAR = [string]$cfg.inventor_year }
    & $cfg.python -m cad_bridge.server
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
