# Installation and troubleshooting

## Requirements

- Windows x64 supported by your installed Autodesk Inventor release.
- Licensed desktop Inventor, candidate range 2017–2027; only 2022 live-tested here.
- CPython x64 3.11–3.14 with pip/venv; [official Python downloads](https://www.python.org/downloads/windows/).
- Codex desktop and a CLI exposing `codex plugin marketplace add` and `codex plugin add`.
- Internet/PyPI during installation. CAD execution uses local COM and stdio; there is no remote bridge server.

Extract the repository to a permanent local folder and double-click `INSTALL.cmd`, or run `install.ps1` in PowerShell. ExecutionPolicy Bypass is scoped to that process; it does not modify machine policy. Review scripts before running downloaded code. Company policy may prohibit execution regardless of this switch.

The installer uses the Python launcher if available. Select a specific interpreter with `-Python 'C:\path\python.exe'`. It creates `%LOCALAPPDATA%\AI CAD Bridge\runtime-0.2.0`, installs the bundled package with pinned dependency constraints, writes `config.json`, and runs the supported Codex marketplace/add commands. It does not launch Inventor, modify its registry, install Autodesk components or touch existing CAD files. Existing config is backed up to `config.json.bak` on rerun.

## Manual route when Codex CLI is unavailable

Run `install.ps1 -SkipCodex`. Then register this repository as a local plugin marketplace using your Codex desktop plugin management interface, if supported by your client. The marketplace file is `.agents/plugins/marketplace.json`. Keep the source folder in place for updates.

Alternatively register the installed runtime as a user MCP server using `codex mcp add` (check your installed CLI help). Use the **python path and workspace printed in config.json**, not a guessed path:

```powershell
$cfg = Get-Content "$env:LOCALAPPDATA\AI CAD Bridge\config.json" -Raw | ConvertFrom-Json
codex mcp add inventor --env "AI_CAD_WORKSPACE=$($cfg.workspace)" -- $cfg.python -m cad_bridge.server
```

This fallback registers the tools only. The plugin skill must be loaded separately or its workflow supplied in the chat. The plugin route is preferred because it bundles both. Do not register both simultaneously.

## Smoke check

Open Inventor manually and run `powershell -File .\doctor.ps1`. It reports the detected version, `tested`/`api_candidate`, running document count and readiness. Then restart Codex and create a new local chat. Ask it to call `inventor_status` and `inventor_schema`.

For custom automated-test installations use `-RuntimeRoot <directory> -SkipCodex` and set `AI_CAD_BRIDGE_CONFIG` to that directory's `config.json` before launching `plugins/ai-cad-bridge/scripts/launch.ps1`.

## Troubleshooting

| Symptom | Action |
|---|---|
| `codex` not found | Add your installed CLI to PATH; reopen terminal; rerun installer or use manual route. |
| Python not found / wrong architecture | Install 64-bit CPython or supply `-Python`. Store aliases may not point to a real interpreter. |
| Dependency download fails | Check proxy/PyPI access; rerun. Do not disable certificate validation. |
| Inventor not available in ROT | Open it manually, wait until ready; use the same Windows account and elevation level as Codex. |
| COM error 0x800700c1 during CLI `--start` | Manual startup may work; check Inventor's registered LocalServer32 through Autodesk repair/support. The installer never rewrites COM registration. |
| Wrong version | Close extra Inventor instances; manually start the desired release. `-InventorYear` only verifies. |
| Missing COM API | Candidate release may be incompatible; collect version and sanitized error in a compatibility issue. |
| Another bridge process is using Inventor | Wait for its operation to finish. Never run parallel CAD operations against the same instance. |
| Input already open | Save and close that source first. The bridge refuses to edit an already-open document. |
| Refusing to overwrite | Choose new output, report, export and preview filenames. |
| Native saved but export failed | Keep the native file; inspect the returned report and use new filenames on retry. |
| Model unit mismatch | JSON accepts mm only; use explicit dimensions. The bridge converts Inventor's internal cm. |
| Tools absent after installation | Restart Codex and begin a new local chat with the plugin selected; check plugin and MCP startup logs. |

## Updates and uninstall

Extract a new release or pull the repository, then rerun `INSTALL.cmd`. The plugin and installed Python package must have the same version. Keep a copy of your previous release/config if you need rollback. Do not edit Codex's plugin cache.

Run `uninstall.ps1` to remove the plugin through Codex. It preserves runtime, config and all CAD files. Inspect and manually remove `%LOCALAPPDATA%\AI CAD Bridge` if no longer needed. Remove a tools-only fallback with `codex mcp remove inventor`. Your CAD workspace is never deleted by these scripts.
