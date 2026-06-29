"""
MCP proxy for Databricks Apps.
Exposes coalesce-transform-mcp (stdio) over Streamable HTTP for Genie.
"""
import os
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

_session: ClientSession | None = None

# Injected automatically by the Databricks Apps runtime
_host = os.environ.get("DATABRICKS_HOST", "")

mcp = FastMCP(
    "coalesce-transform-proxy",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,  # Databricks Apps OAuth handles auth
    ),
)
_srv = mcp._mcp_server


@_srv.list_tools()
async def _list_tools():
    return (await _session.list_tools()).tools


@_srv.call_tool()
async def _call_tool(name: str, arguments: dict | None):
    result = await _session.call_tool(name, arguments or {})
    return result.content


@_srv.list_prompts()
async def _list_prompts():
    return (await _session.list_prompts()).prompts


@_srv.get_prompt()
async def _get_prompt(name: str, arguments: dict | None):
    return await _session.get_prompt(name, arguments or {})


@_srv.list_resources()
async def _list_resources():
    return (await _session.list_resources()).resources


@_srv.read_resource()
async def _read_resource(uri: str):
    result = await _session.read_resource(uri)
    return result.contents


# Build base app first so its lifespan is accessible
_base_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: Starlette):
    global _session
    async with _base_app.router.lifespan_context(app):
        async with stdio_client(
            StdioServerParameters(
                command="npx",
                args=["coalesce-transform-mcp"],
                env={**os.environ},
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                _session = session
                yield
                _session = None


app = Starlette(
    routes=list(_base_app.routes),
    lifespan=lifespan,
)

# CORS — credentials require an explicit origin, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_host] if _host else ["*"],
    allow_credentials=bool(_host),
    allow_methods=["*"],
    allow_headers=["*"],
)