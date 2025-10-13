"""Tool building infrastructure with context-based session injection."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any, TypeAlias

from pydantic_ai import Tool
from typing_extensions import ParamSpec

from pai_browser_use._session import BrowserSession

ToolParams = ParamSpec("ToolParams", default=...)
# Tool functions don't need browser_session parameter
CleanToolFunc: TypeAlias = Callable[ToolParams, Any]

# Use ContextVar to store current browser_session
_browser_session_context: ContextVar[BrowserSession | None] = ContextVar("browser_session", default=None)


def get_browser_session() -> BrowserSession:
    """Get the current browser session from context.

    This function can be called within tool functions to access the browser session.

    Returns:
        Current BrowserSession instance

    Raises:
        RuntimeError: If no browser session is available in current context
    """
    session = _browser_session_context.get()
    if session is None:
        raise RuntimeError("No browser session available in current context")
    return session


def build_tool(
    browser_session: BrowserSession,
    func: CleanToolFunc,
    max_retries: int = 3,
) -> Tool:
    """Build a tool by injecting browser_session through context variables.

    The original function doesn't need browser_session parameter.
    Tool functions can access it via get_browser_session().

    Args:
        browser_session: BrowserSession instance to inject
        func: Tool function to wrap
        max_retries: Maximum number of retries for this tool (default: 3)

    Returns:
        Configured Tool instance
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Set current context's browser_session
        token = _browser_session_context.set(browser_session)
        try:
            return await func(*args, **kwargs)
        finally:
            # Restore context
            _browser_session_context.reset(token)

    # Preserve original function's signature
    wrapper.__signature__ = inspect.signature(func)

    return Tool(
        function=wrapper,
        max_retries=max_retries,
    )
