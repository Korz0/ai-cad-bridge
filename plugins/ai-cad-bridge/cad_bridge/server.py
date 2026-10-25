"""MCP stdio server. COM proxies exist only for the duration of one sync call."""
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from .validation import SCHEMA, validate, Workspace

mcp = FastMCP('AI CAD Bridge', instructions=(
    'Use inventor_schema before composing commands. All dimensions are mm. '
    'Files are scoped to the configured workspace. Run inventor_validate first. '
    'Never claim an API-candidate release is tested.'))


def workspace():
    configured = os.environ.get('AI_CAD_WORKSPACE')
    if not configured:
        raise RuntimeError('AI_CAD_WORKSPACE is not configured. Run install.ps1.')
    root = Path(configured).resolve()
    if not root.is_dir():
        raise RuntimeError('Configured workspace does not exist.')
    return root


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def inventor_schema() -> dict:
    """Return the complete JSON command schema and configured file boundary. No COM access."""
    return {'schema': SCHEMA, 'workspace': str(workspace()), 'units': 'mm'}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def inventor_validate(command: dict) -> dict:
    """Validate structure, measurements and source files without opening Inventor."""
    from .intake import prepare
    validate(command)
    root = workspace()
    from .runner import preflight_paths
    preflight_paths(command, Workspace(root))
    return prepare(command, root)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def inventor_status() -> dict:
    """Read the running Inventor release and compatibility status. Does not start Inventor."""
    from .connector import Connector
    cx = Connector()
    try:
        return {**cx.status(), 'workspace': str(workspace())}
    finally:
        cx.close()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                                     idempotentHint=False, openWorldHint=False))
def inventor_execute(command: dict) -> dict:
    """Execute a validated CAD command, saving only to new files in the workspace.

    Requires Inventor already running. Modify reads a closed source and saves a copy.
    A partial export failure can leave the successfully saved native output; inspect
    success/native_saved before retrying with new filenames. No arbitrary scripts.
    """
    inventor_validate(command)
    from .connector import Connector
    from .runner import Runner
    cx = Connector()
    try:
        return Runner(cx, workspace()).execute(command)
    finally:
        cx.close()


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
