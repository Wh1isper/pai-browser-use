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
# 工具函数不需要 browser_session 参数
CleanToolFunc: TypeAlias = Callable[ToolParams, Any]

# 使用 ContextVar 来存储当前的 browser_session
_browser_session_context: ContextVar[BrowserSession | None] = ContextVar("browser_session", default=None)


def get_browser_session() -> BrowserSession:
    """Get the current browser session from context.

    This function can be called within tool functions to access the browser session.
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
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 设置当前上下文的 browser_session
        token = _browser_session_context.set(browser_session)
        try:
            return await func(*args, **kwargs)
        finally:
            # 恢复上下文
            _browser_session_context.reset(token)

    # 保留原函数的签名信息
    wrapper.__signature__ = inspect.signature(func)

    return Tool(
        function=wrapper,
        max_retries=max_retries,
    )


async def get_page_title() -> str:
    """Get the current page title using browser session."""
    # 通过 get_browser_session() 获取当前的 browser_session
    browser_session = get_browser_session()  # noqa: F841
    # 使用 browser_session ...
    return "Example Title"


TOOLS = [get_page_title]
