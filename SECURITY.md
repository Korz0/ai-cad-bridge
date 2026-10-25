# Security

Treat CAD files and downloaded plugin code as trusted inputs only after review. Inventor is a complex native application; workspace path validation is not a sandbox around Inventor or its file parsers.

The MCP server exposes structured operations, not arbitrary Python/shell execution. Outputs cannot overwrite existing files, inputs must resolve inside the configured workspace, and a Windows mutex prevents concurrent bridge jobs. Reparse-point races or changes by other local processes are outside this boundary. Do not expose this stdio server through an unauthenticated network proxy.

For suspected vulnerabilities, use the repository owner's GitHub private vulnerability reporting channel if enabled. If unavailable, contact the owner privately through their published GitHub profile. Do not post exploit details, sensitive models or credentials in public issues. No private contact address has been invented for this package.
