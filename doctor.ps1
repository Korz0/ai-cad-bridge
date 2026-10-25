param([string]$Config = (Join-Path $env:LOCALAPPDATA 'AI CAD Bridge\config.json'))
$ErrorActionPreference='Stop'
$cfg=Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
$env:AI_CAD_WORKSPACE=$cfg.workspace
if ($cfg.inventor_year) { $env:AI_CAD_INVENTOR_YEAR=[string]$cfg.inventor_year }
& $cfg.python -m cad_bridge.cli --workspace $cfg.workspace status
exit $LASTEXITCODE
