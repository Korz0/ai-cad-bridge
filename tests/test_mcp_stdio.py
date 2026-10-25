"""Real MCP SDK client/server handshake. Does not require Inventor or mutate CAD."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_handshake_validation_and_errors(tmp_path):
    async def check():
        root=Path(__file__).parents[1]
        env=dict(os.environ, AI_CAD_WORKSPACE=str(tmp_path),
                 PYTHONPATH=str(root/'plugins/ai-cad-bridge'))
        params=StdioServerParameters(command=sys.executable,args=['-m','cad_bridge.server'],env=env)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                listing=await session.list_tools()
                assert {t.name for t in listing.tools}=={'inventor_schema','inventor_validate','inventor_status','inventor_execute'}
                assert next(t for t in listing.tools if t.name=='inventor_execute').annotations.readOnlyHint is False
                schema=await session.call_tool('inventor_schema',{})
                assert not schema.isError
                command=json.loads((root/'examples/colored_block.json').read_text())
                result=await session.call_tool('inventor_validate',{'command':command})
                assert not result.isError
                command['output']='../escape.ipt'
                rejected=await session.call_tool('inventor_validate',{'command':command})
                assert rejected.isError
                # Unknown operations cannot reach COM even through execute.
                command['operations']=[{'type':'python','id':'run','depends_on':[]}]
                rejected=await session.call_tool('inventor_execute',{'command':command})
                assert rejected.isError
                assert list(tmp_path.iterdir())==[]
    asyncio.run(check())
