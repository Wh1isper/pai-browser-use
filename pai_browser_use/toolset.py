from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, Self

import httpx
from cdp_use.client import CDPClient
from pydantic_ai import RunContext, Tool
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool
from typing_extensions import TypeVar

from pai_browser_use._logger import logger
from pai_browser_use._session import BrowserSession
from pai_browser_use._tools import build_tool
from pai_browser_use.tools import ALL_TOOLS

AgentDepsT = TypeVar("AgentDepsT", default=None, contravariant=True)
"""Keep this for custom context types in the future."""


def get_cdp_websocket_url(cdp_url: str) -> str:
    logger.info(f"Resolving CDP WebSocket URL from: {cdp_url}")

    # If the URL already starts with ws:// or wss://, treat it as a WebSocket URL
    if cdp_url.startswith(("ws://", "wss://")):
        logger.info(f"Using direct WebSocket URL: {cdp_url}")
        return cdp_url

    # Otherwise, treat it as an HTTP endpoint and fetch the WebSocket URL
    logger.info(f"Fetching WebSocket URL from HTTP endpoint: {cdp_url}")
    response = httpx.get(cdp_url)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as e:  # pragma: no cover
        logger.error(f"Failed to parse CDP response as JSON: {response.text}")
        raise ValueError(f"Invalid CDP response. {response.text}") from e
    if "webSocketDebuggerUrl" not in data:  # pragma: no cover
        logger.error(f"CDP response missing webSocketDebuggerUrl field: {data}")
        raise ValueError(f"Invalid CDP response. {data=}")

    websocket_url = data["webSocketDebuggerUrl"]
    logger.info(f"Resolved WebSocket URL: {websocket_url}")
    return websocket_url


@dataclass(kw_only=True)
class BrowserUseTool(ToolsetTool[AgentDepsT]):
    """A tool definition for a function toolset tool that keeps track of the function to call."""

    call_func: Callable[[dict[str, Any], RunContext[AgentDepsT]], Awaitable[Any]]


class BrowserUseToolset(AbstractToolset, Generic[AgentDepsT]):
    def __init__(
        self,
        cdp_url: str,
        max_retries: int = 3,
        prefix: str | None = None,
        always_use_new_page: bool = False,
    ) -> None:
        self.cdp_url = cdp_url
        self.max_retries = max_retries
        self.prefix = prefix or self.id
        self.always_use_new_page = always_use_new_page

        self._cdp_client: CDPClient | None = None

        self._browser_session: BrowserSession | None = None
        self._tools: list[Tool[AgentDepsT]] | None = None
        self._created_target_id: str | None = None  # Track created page target for cleanup

    @property
    def id(self) -> str | None:
        """An optional identifier for the toolset to distinguish it from other instances of the same class."""
        return "browser_use"

    async def __aenter__(self) -> Self:
        """Enter the toolset context.

        This sets up the CDP client connection and creates or attaches to a page.
        """
        logger.info("Initializing BrowserUseToolset context")

        websocket_url = get_cdp_websocket_url(self.cdp_url)
        logger.info("Connecting to CDP WebSocket...")
        self._cdp_client = await CDPClient(websocket_url).__aenter__()
        logger.info("CDP client connected successfully")

        # Determine whether to reuse existing page or create new one
        if self.always_use_new_page:
            # Always create a new page target
            logger.info("always_use_new_page is True, creating new page...")
            create_response = await self._cdp_client.send.Target.createTarget(params={"url": "about:blank"})
            target_id = create_response["targetId"]
            self._created_target_id = target_id  # Track for cleanup
            logger.info(f"Created new page target: {target_id}")
        else:
            # Get existing targets
            logger.info("Fetching existing browser targets...")
            targets_response = await self._cdp_client.send.Target.getTargets()
            target_infos = targets_response.get("targetInfos", [])
            logger.info(f"Found {len(target_infos)} existing targets")
            logger.debug(
                f"Target list: {[{'targetId': t.get('targetId'), 'type': t.get('type'), 'url': t.get('url', 'N/A')[:50]} for t in target_infos]}"
            )

            # Find existing page target or create new one
            page_target = None
            for target_info in target_infos:
                if target_info.get("type") == "page":
                    page_target = target_info
                    break

            if page_target:
                # Reuse existing page
                target_id = page_target["targetId"]
                logger.info(f"Reusing existing page target: {target_id}")
            else:
                # Create a new page target
                logger.info("No existing page target found, creating new page...")
                create_response = await self._cdp_client.send.Target.createTarget(params={"url": "about:blank"})
                target_id = create_response["targetId"]
                logger.info(f"Created new page target: {target_id}")

        # Attach to the target to get a session
        logger.info(f"Attaching to target {target_id}...")
        attach_response = await self._cdp_client.send.Target.attachToTarget(
            params={"targetId": target_id, "flatten": True}
        )
        session_id = attach_response["sessionId"]

        if session_id is None:  # pragma: no cover
            logger.error("Failed to obtain session ID from target attachment")
            raise ValueError("Failed to get session ID from target attachment")

        logger.info(f"Attached to target, session_id: {session_id}")

        self._browser_session = BrowserSession(
            cdp_client=self._cdp_client,
            page=session_id,  # Store session_id as page reference
        )
        logger.info("BrowserSession created successfully")
        logger.debug(f"Session details - page: {session_id}, viewport: {self._browser_session.viewport}")

        # Rebuild tools with actual session
        logger.info(f"Building {len(ALL_TOOLS)} browser tools...")
        self._tools = [
            build_tool(
                self._browser_session,
                tool,
                max_retries=self.max_retries,
            )
            for tool in ALL_TOOLS
        ]
        logger.info("All tools built and ready")
        logger.debug(f"Tool names: {[tool.tool_def.name for tool in self._tools]}")

        return self

    async def __aexit__(self, *args: Any) -> bool | None:
        """Exit the toolset context.

        This tears down the CDP client connection and closes created page if needed.
        """
        logger.info("Cleaning up BrowserUseToolset context")

        # Close the created page target if we created one
        if self._created_target_id and self._cdp_client:
            try:
                logger.info(f"Closing created page target: {self._created_target_id}")
                await self._cdp_client.send.Target.closeTarget(params={"targetId": self._created_target_id})
                logger.info(f"Successfully closed page target: {self._created_target_id}")
            except Exception as e:  # pragma: no cover
                logger.warning(f"Failed to close page target {self._created_target_id}: {e}")
            finally:
                self._created_target_id = None

        if self._cdp_client:
            logger.info("Closing CDP client connection...")
            await self._cdp_client.__aexit__(*args)
            self._cdp_client = None
            logger.info("CDP client connection closed")

        if self._browser_session:
            logger.info("Disposing browser session...")
            logger.debug(
                f"Session state before disposal - URL: {self._browser_session.current_url}, History: {len(self._browser_session.navigation_history)} entries"
            )
            self._browser_session.dispose()
            logger.info("Browser session disposed")
        self._tools = None
        return None

    async def get_tools(self, ctx: RunContext[AgentDepsT]) -> dict[str, BrowserUseTool[AgentDepsT]]:
        """The tools that are available in this toolset. Similar to FunctionToolset but no need to handle prepare"""
        return {
            f"{self.prefix}_{tool.name}": BrowserUseTool(
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
        tool: BrowserUseTool[AgentDepsT],
    ) -> Any:
        """Call a tool with the given arguments.

        Args:
            name: The name of the tool to call.
            tool_args: The arguments to pass to the tool.
            ctx: The run context.
            tool: The tool definition returned by [`get_tools`][pydantic_ai.toolsets.AbstractToolset.get_tools] that was called.
        """
        return await tool.call_func(tool_args, ctx)
