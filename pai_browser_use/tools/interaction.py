"""Interaction tools for browser control."""

from __future__ import annotations

from typing import Any

from pai_browser_use._tools import BrowserSession, get_browser_session
from pai_browser_use.tools._types import ClickResult, ExecuteScriptResult, TypeTextResult


async def click_element(selector: str) -> dict[str, Any]:
    """Click an element on the page.

    Args:
        selector: CSS selector for the element

    Returns:
        ClickResult dictionary
    """
    session = get_browser_session()

    try:
        # Enable DOM
        await session.cdp_client.send.DOM.enable(session_id=session.page)

        # Get document and find element
        doc = await session.cdp_client.send.DOM.getDocument(session_id=session.page)
        root_node_id = doc["root"]["nodeId"]

        result = await session.cdp_client.send.DOM.querySelector(
            params={
                "nodeId": root_node_id,
                "selector": selector,
            },
            session_id=session.page,
        )

        node_id = result.get("nodeId")
        if not node_id or node_id == 0:
            return ClickResult(
                status="not_found",
                selector=selector,
                error_message=f"Element not found: {selector}",
            ).model_dump()

        # Get box model
        box_result = await session.cdp_client.send.DOM.getBoxModel(params={"nodeId": node_id}, session_id=session.page)
        border = box_result["model"]["border"]

        # Calculate center point
        x = (border[0] + border[4]) / 2
        y = (border[1] + border[5]) / 2

        element_info = {
            "x": x,
            "y": y,
            "width": border[4] - border[0],
            "height": border[5] - border[1],
        }

        # Perform click using Input domain
        await session.cdp_client.send.Input.dispatchMouseEvent(
            params={
                "type": "mousePressed",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
            session_id=session.page,
        )

        await session.cdp_client.send.Input.dispatchMouseEvent(
            params={
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
            session_id=session.page,
        )

        # Wait a moment
        import asyncio

        await asyncio.sleep(0.5)

        return ClickResult(
            status="success",
            selector=selector,
            element_info=element_info,
        ).model_dump()

    except Exception as e:
        return ClickResult(
            status="error",
            selector=selector,
            error_message=str(e),
        ).model_dump()


async def type_text(selector: str, text: str, clear_first: bool = True) -> dict[str, Any]:
    """Type text into an input element.

    Args:
        selector: CSS selector for the input element
        text: Text to type
        clear_first: Clear existing text before typing (default: True)

    Returns:
        TypeTextResult dictionary
    """
    session = get_browser_session()

    try:
        # First click the element to focus
        click_result = await click_element(selector)
        if click_result["status"] != "success":
            return TypeTextResult(
                status=click_result["status"],
                selector=selector,
                text=text,
                error_message=click_result.get("error_message"),
            ).model_dump()

        # Clear if requested
        if clear_first:
            # Select all (Cmd+A or Ctrl+A)
            is_mac = await _is_mac(session)
            await session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    "type": "keyDown",
                    "key": "a",
                    "code": "KeyA",
                    "modifiers": 8 if is_mac else 2,  # 8=Cmd, 2=Ctrl
                },
                session_id=session.page,
            )
            await session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    "type": "keyUp",
                    "key": "a",
                    "code": "KeyA",
                },
                session_id=session.page,
            )

            # Delete
            await session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    "type": "keyDown",
                    "key": "Backspace",
                    "code": "Backspace",
                },
                session_id=session.page,
            )
            await session.cdp_client.send.Input.dispatchKeyEvent(
                params={
                    "type": "keyUp",
                    "key": "Backspace",
                    "code": "Backspace",
                },
                session_id=session.page,
            )

        # Type each character
        for char in text:
            await session.cdp_client.send.Input.insertText(params={"text": char}, session_id=session.page)

        return TypeTextResult(
            status="success",
            selector=selector,
            text=text,
        ).model_dump()

    except Exception as e:
        return TypeTextResult(
            status="error",
            selector=selector,
            text=text,
            error_message=str(e),
        ).model_dump()


async def execute_javascript(script: str) -> dict[str, Any]:
    """Execute JavaScript code in the page context.

    Args:
        script: JavaScript code to execute

    Returns:
        ExecuteScriptResult dictionary with result or error
    """
    session = get_browser_session()

    try:
        # Execute script
        result = await session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": script,
                "returnByValue": True,
            },
            session_id=session.page,
        )

        if "exceptionDetails" in result:
            return ExecuteScriptResult(
                status="error",
                error_message=str(result["exceptionDetails"]),
            ).model_dump()

        return ExecuteScriptResult(
            status="success",
            result=result.get("result", {}).get("value"),
        ).model_dump()

    except Exception as e:
        return ExecuteScriptResult(
            status="error",
            error_message=str(e),
        ).model_dump()


async def scroll_to(x: int = 0, y: int = 0) -> dict[str, Any]:
    """Scroll the page to specified coordinates.

    Args:
        x: Horizontal scroll position (default: 0)
        y: Vertical scroll position (default: 0)

    Returns:
        ExecuteScriptResult dictionary
    """
    return await execute_javascript(f"window.scrollTo({x}, {y})")


async def _is_mac(session: BrowserSession) -> bool:
    """Check if platform is Mac."""
    result = await session.cdp_client.send.Runtime.evaluate(
        params={
            "expression": "navigator.platform.toLowerCase().includes('mac')",
            "returnByValue": True,
        },
        session_id=session.page,
    )
    return result["result"]["value"]
