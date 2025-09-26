from __future__ import annotations

from typing import Any, Generic, Self

import httpx
from cdp_use.client import CDPClient
from pydantic_ai import RunContext
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool
from typing_extensions import TypeVar

AgentDepsT = TypeVar("AgentDepsT", default=None, contravariant=True)
"""Keep this for custom context types in the future."""


def get_cdp_websocket_url(cdp_url: str) -> str:
    # If the URL already starts with ws:// or wss://, treat it as a WebSocket URL
    if cdp_url.startswith(("ws://", "wss://")):
        return cdp_url

    # Otherwise, treat it as an HTTP endpoint and fetch the WebSocket URL
    response = httpx.get(cdp_url)
    response.raise_for_status()
    data = response.json()
    if "webSocketDebuggerUrl" not in data:
        raise ValueError(f"Invalid CDP response. {data=}")
    return data["webSocketDebuggerUrl"]


class BrowserUseToolset(AbstractToolset, Generic[AgentDepsT]):
    def __init__(self, cdp_url: str) -> None:
        self.cdp_url = cdp_url
        self._cdp_client: CDPClient | None = None

    @property
    def id(self) -> str | None:
        """An optional identifier for the toolset to distinguish it from other instances of the same class."""
        return "browser-use"

    async def __aenter__(self) -> Self:
        """Enter the toolset context.

        This sets up the CDP client connection.
        """
        websocket_url = get_cdp_websocket_url(self.cdp_url)
        self._cdp_client = await CDPClient(websocket_url).__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> bool | None:
        """Exit the toolset context.

        This tears down the CDP client connection.
        """
        if self._cdp_client:
            await self._cdp_client.__aexit__(*args)
            self._cdp_client = None
        return None

    async def get_tools(self, ctx: RunContext[AgentDepsT]) -> dict[str, ToolsetTool[AgentDepsT]]:
        """The tools that are available in this toolset."""
        raise NotImplementedError()

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[AgentDepsT],
        tool: ToolsetTool[AgentDepsT],
    ) -> Any:
        """Call a tool with the given arguments.

        Args:
            name: The name of the tool to call.
            tool_args: The arguments to pass to the tool.
            ctx: The run context.
            tool: The tool definition returned by [`get_tools`][pydantic_ai.toolsets.AbstractToolset.get_tools] that was called.
        """
        raise NotImplementedError()
