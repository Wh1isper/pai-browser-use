"""Navigation tools for browser control."""

from __future__ import annotations

import json
from typing import Any

from pai_browser_use._tools import get_browser_session
from pai_browser_use.tools._types import NavigationResult


async def navigate_to_url(url: str, timeout: int = 30000) -> dict[str, Any]:
    """Navigate to a URL.

    Args:
        url: Target URL to navigate to
        timeout: Navigation timeout in milliseconds (default: 30000)

    Returns:
        NavigationResult dictionary with status, url, and title
    """
    session = get_browser_session()

    try:
        # Enable Page domain
        await session.cdp_client.send.Page.enable(session_id=session.page)

        # Navigate via CDP
        await session.cdp_client.send.Page.navigate(params={"url": url}, session_id=session.page)

        # Wait a moment for navigation to complete
        import asyncio

        await asyncio.sleep(1)

        # Get page info after navigation
        result = await session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": """
                    JSON.stringify({
                        url: window.location.href,
                        title: document.title
                    })
                """,
                "returnByValue": True,
            },
            session_id=session.page,
        )

        info = json.loads(result["result"]["value"])

        # Update session state
        session.current_url = info["url"]
        session.current_title = info["title"]
        session.navigation_history.append(info["url"])

        return NavigationResult(
            status="success",
            url=info["url"],
            title=info["title"],
        ).model_dump()

    except TimeoutError:
        return NavigationResult(
            status="timeout",
            url=url,
            error_message=f"Navigation timeout after {timeout}ms",
        ).model_dump()

    except Exception as e:
        return NavigationResult(
            status="error",
            url=url,
            error_message=str(e),
        ).model_dump()


async def go_back() -> dict[str, Any]:
    """Navigate back in browser history.

    Returns:
        NavigationResult dictionary
    """
    session = get_browser_session()

    try:
        # Get navigation history
        history = await session.cdp_client.send.Page.getNavigationHistory(session_id=session.page)

        current_index = history["currentIndex"]
        if current_index > 0:
            # Navigate to previous entry
            entry_id = history["entries"][current_index - 1]["id"]
            await session.cdp_client.send.Page.navigateToHistoryEntry(
                params={"entryId": entry_id}, session_id=session.page
            )

            # Wait and get updated info
            import asyncio

            await asyncio.sleep(0.5)

            result = await session.cdp_client.send.Runtime.evaluate(
                params={
                    "expression": """
                        JSON.stringify({
                            url: window.location.href,
                            title: document.title
                        })
                    """,
                    "returnByValue": True,
                },
                session_id=session.page,
            )

            info = json.loads(result["result"]["value"])

            session.current_url = info["url"]
            session.current_title = info["title"]

            return NavigationResult(
                status="success",
                url=info["url"],
                title=info["title"],
            ).model_dump()
        else:
            return NavigationResult(
                status="error",
                url=session.current_url,
                error_message="No previous page in history",
            ).model_dump()

    except Exception as e:
        return NavigationResult(
            status="error",
            url=session.current_url,
            error_message=str(e),
        ).model_dump()


async def go_forward() -> dict[str, Any]:
    """Navigate forward in browser history.

    Returns:
        NavigationResult dictionary
    """
    session = get_browser_session()

    try:
        # Get navigation history
        history = await session.cdp_client.send.Page.getNavigationHistory(session_id=session.page)

        current_index = history["currentIndex"]
        if current_index < len(history["entries"]) - 1:
            # Navigate to next entry
            entry_id = history["entries"][current_index + 1]["id"]
            await session.cdp_client.send.Page.navigateToHistoryEntry(
                params={"entryId": entry_id}, session_id=session.page
            )

            # Wait and get updated info
            import asyncio

            await asyncio.sleep(0.5)

            result = await session.cdp_client.send.Runtime.evaluate(
                params={
                    "expression": """
                        JSON.stringify({
                            url: window.location.href,
                            title: document.title
                        })
                    """,
                    "returnByValue": True,
                },
                session_id=session.page,
            )

            info = json.loads(result["result"]["value"])

            session.current_url = info["url"]
            session.current_title = info["title"]

            return NavigationResult(
                status="success",
                url=info["url"],
                title=info["title"],
            ).model_dump()
        else:
            return NavigationResult(
                status="error",
                url=session.current_url,
                error_message="No next page in history",
            ).model_dump()

    except Exception as e:
        return NavigationResult(
            status="error",
            url=session.current_url,
            error_message=str(e),
        ).model_dump()


async def reload_page(ignore_cache: bool = False) -> dict[str, Any]:
    """Reload the current page.

    Args:
        ignore_cache: If True, reload ignoring cache

    Returns:
        NavigationResult dictionary
    """
    session = get_browser_session()

    try:
        # Reload using CDP
        await session.cdp_client.send.Page.reload(params={"ignoreCache": ignore_cache}, session_id=session.page)

        # Wait for reload
        import asyncio

        await asyncio.sleep(1)

        # Get updated page info
        result = await session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": """
                    JSON.stringify({
                        url: window.location.href,
                        title: document.title
                    })
                """,
                "returnByValue": True,
            },
            session_id=session.page,
        )

        info = json.loads(result["result"]["value"])

        session.current_url = info["url"]
        session.current_title = info["title"]

        return NavigationResult(
            status="success",
            url=info["url"],
            title=info["title"],
        ).model_dump()

    except Exception as e:
        return NavigationResult(
            status="error",
            url=session.current_url,
            error_message=str(e),
        ).model_dump()
