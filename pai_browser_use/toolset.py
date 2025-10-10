from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, Self

import httpx
from cdp_use.client import CDPClient
from pydantic_ai import RunContext
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool
from typing_extensions import TypeVar

from pai_browser_use._session import BrowserSession
from pai_browser_use._tools import TOOLS, build_tool

AgentDepsT = TypeVar("AgentDepsT", default=None, contravariant=True)
"""Keep this for custom context types in the future."""


def get_cdp_websocket_url(cdp_url: str) -> str:
    # If the URL already starts with ws:// or wss://, treat it as a WebSocket URL
    if cdp_url.startswith(("ws://", "wss://")):
        return cdp_url

    # Otherwise, treat it as an HTTP endpoint and fetch the WebSocket URL
    response = httpx.get(cdp_url)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as e:
        raise ValueError(f"Invalid CDP response. {response.text}") from e
    if "webSocketDebuggerUrl" not in data:
        raise ValueError(f"Invalid CDP response. {data=}")
    return data["webSocketDebuggerUrl"]


@dataclass(kw_only=True)
class BrowserUseTool(ToolsetTool[AgentDepsT]):
    """A tool definition for a function toolset tool that keeps track of the function to call."""

    call_func: Callable[[dict[str, Any], RunContext[AgentDepsT]], Awaitable[Any]]


class BrowserUseToolset(AbstractToolset, Generic[AgentDepsT]):
    def __init__(self, cdp_url: str) -> None:
        self.cdp_url = cdp_url
        self._cdp_client: CDPClient | None = None

        self._browser_session = BrowserSession()
        self._tools = [build_tool(self._browser_session, tool) for tool in TOOLS]

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

    async def get_tools(self, ctx: RunContext[AgentDepsT]) -> dict[str, BrowserUseTool[AgentDepsT]]:
        """The tools that are available in this toolset. Similar to FunctionToolset but no need to handle prepare"""
        return {
            tool.name: BrowserUseTool(
                toolset=self,
                tool_def=tool.tool_def,
                max_retries=tool.max_retries,
                args_validator=tool.function_schema.validator,
                call_func=tool.function_schema.call,
            )
            for tool in self._tools
        }

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
        return await tool.call_func(tool_args, ctx)
