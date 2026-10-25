# AI CAD Bridge for Codex

Download the [installable release](https://github.com/Korz0/ai-cad-bridge/releases/tag/v0.2.0).

Create native Autodesk Inventor parts and assemblies from natural-language requests through a local MCP plugin. Dimensions are in **millimeters**. Runs on Windows with your installed, licensed Inventor.

**Release 0.2.0 — beta.** Inventor 2022 has real integration-test evidence. Inventor 2017–2021 and 2023–2027 are **API-compatible candidates, not certified or live-tested releases**. See [compatibility and Autodesk sources](docs/COMPATIBILITY.md).

[Español](README.es.md) · [Installation](docs/INSTALL.md) · [Commands](docs/COMMANDS.md) · [Testing](docs/TESTING.md) · [Privacy](PRIVACY.md)

## Install

1. Install **64-bit Python 3.11–3.14**, Codex desktop/CLI with plugin support, and Autodesk Inventor. Use a Windows version supported by your Inventor release.
2. Download this repository using GitHub **Code → Download ZIP**, or a source ZIP from Releases. Extract it to a permanent folder.
3. Double-click **INSTALL.cmd**. The installer creates an isolated Python environment, downloads dependencies from PyPI, registers the local plugin marketplace and installs the plugin. No administrator rights are required.
4. Open Inventor, restart Codex and start a **new local chat** with **AI CAD Bridge** selected.

Default CAD workspace: `Documents\AI CAD Bridge`. Place input parts, photographs and drawings there. Existing outputs are never overwritten.

Advanced installation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Workspace "D:\CAD\AI" -InventorYear 2022
```

The year option verifies the attached release; it does not launch or switch versions. Keep one intended Inventor instance running. If Codex CLI is not on PATH, see the [manual installation route](docs/INSTALL.md).

## Try it

> Use AI CAD Bridge to create a 40 × 30 × 10 mm block, as a single solid with one feature. Color its top face blue and the rest black. Save colored_block.ipt and a preview, then verify the dimensions.

> Create a 100 × 60 × 10 mm plate with an 8 mm through-hole centered at X=20, Y=20. Save a native IPT and STEP copy.

> Inspect the closed part in input.ipt. Report its dimensions and solid-body count without modifying it.

The agent interprets your request and available images, then sends a validated command to Inventor. **The server is not an independent image-to-CAD model.** Exact dimensions require measurements or reliable manufacturer data; image-derived dimensions remain estimates.

## Included

- Four MCP tools: `inventor_status`, `inventor_schema`, `inventor_validate`, `inventor_execute`.
- Sketch rectangles, circles, lines and arcs; constraints and dimensions.
- Extrusions, revolutions, holes, fillets, chamfers, patterns, mirror and offset workplanes.
- Assembly occurrences and origin-plane mate/flush constraints.
- Modify a closed source into a new file, with persistent feature references.
- Optional single-solid/one-feature consolidation, exact envelope checks and per-face RGB appearances.
- Native IPT/IAM, STEP/STL export and PNG/BMP snapshots.
- Transaction rollback, operation health/volume checks, explicit estimates and workspace-scoped file access.

Not implemented: drawing generation, CAM, arbitrary Python execution, arbitrary feature types, sheet-metal unfolding, automatic photogrammetry, or control of multiple Inventor instances. Face colors are visual appearances, not multi-material physical properties. Monolithic output deliberately removes editable construction history; retain its command report to rebuild.

## Compatibility and distribution

This is a **community local plugin**, not an Autodesk add-in or an official OpenAI/Autodesk product. It communicates with Inventor's documented COM Automation API from an external Python process. It does not redistribute Autodesk binaries or grant an Inventor license.

This repository is prepared for GitHub/manual distribution. It has not been submitted to or approved by the OpenAI public plugin directory. Public local-MCP submissions have separate eligibility/review requirements: [official desktop-plugin guidance](https://developers.openai.com/plugins/deploy/desktop-only).

## Development

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -c requirements-lock.txt -e .\plugins\ai-cad-bridge pytest
.\.venv\Scripts\python -m pytest -q
```

Windows CI checks validation and a real MCP protocol handshake without Inventor. CAD integration tests are explicit opt-in; they create files in a new test directory and require a licensed installation. See [testing](docs/TESTING.md), [contributing](CONTRIBUTING.md) and [release preparation](docs/RELEASING.md).

## License

MIT for this project's source. Dependencies retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md). Autodesk, Inventor, OpenAI and Codex are trademarks of their respective owners. No affiliation or endorsement is implied.
