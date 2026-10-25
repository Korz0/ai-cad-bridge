# AI CAD Bridge plugin component

This folder contains the portable plugin, compatibility manifest, MCP server and modeling skill.

For the easy installer, download the **source/repository ZIP** of the same release and run `INSTALL.cmd` from its root. The standalone plugin ZIP requires that runtime installation first; importing this folder alone does not install Python dependencies.

Runtime configuration defaults to `%LOCALAPPDATA%\AI CAD Bridge\config.json`. The launcher verifies its version and uses the installed isolated Python environment. No Autodesk software is bundled.

See `docs/COMPATIBILITY.md` for the tested/candidate distinction and official Autodesk references. See `examples/colored_block.json` for monolithic geometry and face appearances. Full installation/testing documentation lives in the source repository ZIP. Source is licensed under the included MIT license.
