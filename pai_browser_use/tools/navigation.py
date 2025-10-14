"""Navigation tools for browser control."""

from __future__ import annotations

import json
from typing import Any

from pai_browser_use._logger import logger
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
    logger.info(f"Starting navigation to URL: {url} (timeout: {timeout}ms)")
    session = get_browser_session()

    try:
        # Enable Page domain
        logger.info("Enabling Page domain...")
        await session.cdp_client.send.Page.enable(session_id=session.page)

        # Navigate via CDP
        logger.info(f"Sending CDP Page.navigate command for: {url}")
        await session.cdp_client.send.Page.navigate(params={"url": url}, session_id=session.page)

        # Wait a moment for navigation to complete
        import asyncio

        logger.info("Waiting for navigation to complete...")
        await asyncio.sleep(1)

        # Get page info after navigation
        logger.info("Fetching page information after navigation...")
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
        logger.info(f"Navigation successful - URL: {info['url']}, Title: {info['title']}")
        logger.debug(f"Full navigation info: {info}")

        # Update session state
        session.current_url = info["url"]
        session.current_title = info["title"]
        session.navigation_history.append(info["url"])
        logger.info(f"Session state updated, navigation history length: {len(session.navigation_history)}")

        return NavigationResult(
            status="success",
            url=info["url"],
            title=info["title"],
        ).model_dump()

    except TimeoutError:  # pragma: no cover
        logger.warning(f"Navigation timeout after {timeout}ms for URL: {url}")
        return NavigationResult(
            status="timeout",
            url=url,
            error_message=f"Navigation timeout after {timeout}ms",
        ).model_dump()

    except Exception as e:  # pragma: no cover
        logger.error(f"Navigation failed for URL {url}: {e}")
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
    logger.info("Attempting to navigate back in history")
    session = get_browser_session()

    try:
        # Get navigation history
        logger.info("Fetching navigation history...")
        history = await session.cdp_client.send.Page.getNavigationHistory(session_id=session.page)

        current_index = history["currentIndex"]
        logger.info(f"Current history index: {current_index}, total entries: {len(history['entries'])}")

        if current_index > 0:
            # Navigate to previous entry
            entry_id = history["entries"][current_index - 1]["id"]
            logger.info(f"Navigating back to history entry: {entry_id}")
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
            logger.debug(f"Page info after going back: {info}")

            session.current_url = info["url"]
            session.current_title = info["title"]
            logger.info(f"Successfully navigated back to: {info['url']}")

            return NavigationResult(
                status="success",
                url=info["url"],
                title=info["title"],
            ).model_dump()
        else:
            logger.warning("Cannot go back - already at the first page in history")
            return NavigationResult(
                status="error",
                url=session.current_url,
                error_message="No previous page in history",
            ).model_dump()

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to navigate back: {e}")
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
    logger.info("Attempting to navigate forward in history")
    session = get_browser_session()

    try:
        # Get navigation history
        logger.info("Fetching navigation history...")
        history = await session.cdp_client.send.Page.getNavigationHistory(session_id=session.page)

        current_index = history["currentIndex"]
        logger.info(f"Current history index: {current_index}, total entries: {len(history['entries'])}")

        if current_index < len(history["entries"]) - 1:
            # Navigate to next entry
            entry_id = history["entries"][current_index + 1]["id"]
            logger.info(f"Navigating forward to history entry: {entry_id}")
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
            logger.debug(f"Page info after going forward: {info}")

            session.current_url = info["url"]
            session.current_title = info["title"]
            logger.info(f"Successfully navigated forward to: {info['url']}")

            return NavigationResult(
                status="success",
                url=info["url"],
                title=info["title"],
            ).model_dump()
        else:
            logger.warning("Cannot go forward - already at the last page in history")
            return NavigationResult(
                status="error",
                url=session.current_url,
                error_message="No next page in history",
            ).model_dump()

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to navigate forward: {e}")
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
    logger.info(f"Reloading page (ignore_cache: {ignore_cache})")
    session = get_browser_session()

    try:
        # Reload using CDP
        logger.info("Sending CDP Page.reload command...")
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
        logger.debug(f"Page info after reload: {info}")

        session.current_url = info["url"]
        session.current_title = info["title"]
        logger.info(f"Page reloaded successfully: {info['url']}")

        return NavigationResult(
            status="success",
            url=info["url"],
            title=info["title"],
        ).model_dump()

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to reload page: {e}")
        return NavigationResult(
            status="error",
            url=session.current_url,
            error_message=str(e),
        ).model_dump()
