# Privacy

The bridge runs locally, communicates with Inventor through COM, and exposes tools to its parent client over stdio. It has no telemetry, hosted service, account system or built-in network upload. Installation downloads Python dependencies from PyPI; Codex manages its own plugin installation and model connections.

Tool arguments, tool results, measurements and images supplied to Codex are handled under your Codex/OpenAI account and organizational settings. Local CAD execution does **not** mean the surrounding AI conversation is offline. This project does not control those services.

The configured workspace limits files accepted by the bridge. Output reports store commands, source hashes, version information and local paths. Source file contents are not uploaded by this server, but the agent/client may read them separately with your authorization. Review reports before sharing them publicly.

Configuration is stored under your LocalAppData; CAD files remain in your chosen workspace. Uninstall preserves both. The plugin requests no API key or Autodesk password.
