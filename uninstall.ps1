$ErrorActionPreference='Stop'
& codex plugin remove 'ai-cad-bridge@ai-cad-bridge-community'
if ($LASTEXITCODE -ne 0) { throw 'Codex could not remove the plugin.' }
Write-Host 'Plugin removed. CAD files and runtime are preserved.'
Write-Host 'Optional: remove AI CAD Bridge from LocalAppData manually after checking config.json.'
