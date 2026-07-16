"""
MCPDataHubClient
-----------------
This is PhoenixForge AI's real integration with the DataHub MCP Server
(package: mcp-server-datahub, https://github.com/acryldata/mcp-server-datahub),
which is one of the four DataHub integration surfaces required by the hackathon rules
(MCP Server / Agent Context Kit / DataHub Skills / Analytics Agent).

It launches the official server as a subprocess over stdio using the standard `mcp`
Python SDK and calls its real tools: search, get_lineage, list_schema_fields,
entity/schema lookups, and (when TOOLS_IS_MUTATION_ENABLED=true on the server)
mutation tools such as add_tags, update_description, and save_document.

Design choice: tool names are resolved dynamically via list_tools() instead of
hardcoded, because mcp-server-datahub's exact tool names have changed across
versions (see its CHANGELOG). We match by keyword against the live tool list, so
this client keeps working even if a future server version renames a tool.

If the server process can't be started or the connection fails (no DataHub
instance available, package not installed, etc.), every method raises
MCPUnavailableError. The caller (datahub_client.py) catches this and falls back to
DEMO_MODE data, so the full agent pipeline still runs end-to-end with zero
DataHub infrastructure -- which is how judges will run it most of the time.
"""
import asyncio
import shlex
from contextlib import AsyncExitStack
from typing import Any, Optional

from .config import settings


class MCPUnavailableError(RuntimeError):
    pass


class MCPDataHubClient:
    def __init__(self):
        self._session = None
        self._stack: Optional[AsyncExitStack] = None
        self._tool_names: list[str] = []
        self._connected = False

    # ------------------------------------------------------------------ #
    # Connection lifecycle
    # ------------------------------------------------------------------ #
    async def connect(self):
        if self._connected:
            return
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as e:
            raise MCPUnavailableError(
                "The 'mcp' package is not installed. Run: pip install mcp --break-system-packages"
            ) from e

        command_parts = shlex.split(settings.MCP_SERVER_COMMAND)
        env = {
            "DATAHUB_GMS_URL": settings.DATAHUB_GMS_URL,
            "DATAHUB_GMS_TOKEN": settings.DATAHUB_TOKEN,
        }
        if settings.MCP_ENABLE_MUTATIONS:
            env["TOOLS_IS_MUTATION_ENABLED"] = "true"

        server_params = StdioServerParameters(
            command=command_parts[0],
            args=command_parts[1:],
            env=env,
        )

        self._stack = AsyncExitStack()
        try:
            read, write = await self._stack.enter_async_context(stdio_client(server_params))
            self._session = await self._stack.enter_async_context(ClientSession(read, write))
            await self._session.initialize()
            tools_result = await self._session.list_tools()
            self._tool_names = [t.name for t in tools_result.tools]
            self._connected = True
        except Exception as e:
            await self._stack.aclose()
            raise MCPUnavailableError(f"Could not start/connect to DataHub MCP Server: {e}") from e

    async def close(self):
        if self._stack:
            await self._stack.aclose()
        self._connected = False

    def _resolve(self, *keywords: str) -> str:
        """Find the live tool whose name contains all given keywords (case-insensitive)."""
        for name in self._tool_names:
            lname = name.lower()
            if all(k in lname for k in keywords):
                return name
        raise MCPUnavailableError(
            f"No tool matching {keywords} found on connected MCP server. "
            f"Available tools: {self._tool_names}"
        )

    async def _call(self, *keywords: str, **arguments) -> Any:
        if not self._connected:
            await self.connect()
        tool_name = self._resolve(*keywords)
        result = await self._session.call_tool(tool_name, arguments=arguments)
        if result.isError:
            raise MCPUnavailableError(f"MCP tool '{tool_name}' returned an error: {result.content}")
        return result.content

    # ------------------------------------------------------------------ #
    # Read tools
    # ------------------------------------------------------------------ #
    async def search(self, query: str, limit: int = 10) -> Any:
        return await self._call("search", query=query, limit=limit)

    async def get_lineage(self, urn: str, direction: str = "both", hops: int = 3) -> Any:
        return await self._call("lineage", urn=urn, direction=direction)

    async def get_entities(self, urns: list[str]) -> Any:
        return await self._call("entit", urns=urns)

    async def list_schema_fields(self, urn: str) -> Any:
        return await self._call("schema", "field", urn=urn)

    async def get_dataset_queries(self, urn: str) -> Any:
        return await self._call("dataset", "quer", urn=urn)

    # ------------------------------------------------------------------ #
    # Mutation tools (require MCP_ENABLE_MUTATIONS=true)
    # ------------------------------------------------------------------ #
    async def add_tags(self, urn: str, tags: list[str]) -> Any:
        return await self._call("add", "tag", urn=urn, tags=tags)

    async def update_description(self, urn: str, description: str) -> Any:
        return await self._call("update", "description", urn=urn, description=description)

    async def save_document(self, title: str, content: str) -> Any:
        return await self._call("save", "document", title=title, content=content)


# Singleton, connected lazily on first use
mcp_datahub_client = MCPDataHubClient()


def run_async(coro):
    """Small helper so synchronous agent code (FastAPI routes, scripts) can call
    the async MCP client without every caller needing to be async itself."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already inside an event loop (e.g. FastAPI async route) -- caller
            # should await the coroutine directly instead of using this helper.
            raise RuntimeError("run_async() called from within a running event loop; await the coroutine directly.")
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
