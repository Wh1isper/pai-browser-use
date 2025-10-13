"""State inspection and screenshot tools."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

from pydantic_ai.messages import ToolReturn

from pai_browser_use._image_utils import ImageMediaType, split_image_data
from pai_browser_use._tools import get_browser_session
from pai_browser_use.tools._types import (
    ElementScreenshotResult,
    PageInfo,
    ScreenshotResult,
)


async def get_page_info() -> dict[str, Any]:
    """Get current page basic information.

    Returns:
        PageInfo dictionary with url, title, ready_state, and viewport
    """
    session = get_browser_session()

    # Execute JS to get page info
    result = await session.cdp_client.send.Runtime.evaluate(
        params={
            "expression": """
                JSON.stringify({
                    url: window.location.href,
                    title: document.title,
                    readyState: document.readyState,
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

    return PageInfo(
        url=info["url"],
        title=info["title"],
        ready_state=info["readyState"],
        viewport=session.viewport,
    ).model_dump()


async def get_page_content(content_format: str = "text") -> str:
    """Get current page content.

    Args:
        content_format: Content format - "html" or "text" (default: "text")

    Returns:
        Page content as string
    """
    session = get_browser_session()

    if content_format == "html":
        # Get HTML content
        result = await session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": "document.documentElement.outerHTML",
                "returnByValue": True,
            },
            session_id=session.page,
        )
        return result["result"]["value"]
    else:  # text
        result = await session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": "document.body.innerText",
                "returnByValue": True,
            },
            session_id=session.page,
        )
        return result["result"]["value"]


async def take_screenshot(
    full_page: bool = False,
    img_format: ImageMediaType = "image/png",
) -> ToolReturn:
    """Capture screenshot of current page.

    Long pages are automatically split into segments (max 20).

    Args:
        full_page: Capture full scrollable page or just viewport (default: False)
        img_format: Image format - "image/png", "image/jpeg", or "image/webp" (default: "image/png")

    Returns:
        ToolReturn with:
        - return_value: ScreenshotResult with metadata
        - content: List of BinaryContent (image segments)
    """
    session = get_browser_session()

    try:
        # Extract format suffix (image/png -> png)
        format_suffix = img_format.split("/")[1] if "/" in img_format else img_format

        # Capture screenshot via CDP
        params: dict[str, Any] = {"format": format_suffix}
        if full_page:
            params["captureBeyondViewport"] = True

        result = await session.cdp_client.send.Page.captureScreenshot(params=params, session_id=session.page)
        screenshot_data = result["data"]

        # Convert base64 to bytes
        image_bytes = base64.b64decode(screenshot_data)

        # Split image if needed
        segments = split_image_data(
            image_bytes=image_bytes,
            max_height=4096,
            overlap=50,
            media_type=img_format,
        )

        # Limit to 20 segments
        truncated = len(segments) > 20
        if truncated:
            segments = segments[:20]

        # Update session state
        session.last_screenshot_timestamp = time.time()

        # Build return value
        result_obj = ScreenshotResult(
            status="success",
            url=session.current_url,
            segments_count=len(segments),
            truncated=truncated,
            format=format_suffix,
            full_page=full_page,
        )

        # Return with multi-modal content
        return ToolReturn(
            return_value=result_obj.model_dump(),
            content=segments,  # List of BinaryContent
        )

    except Exception as e:
        # Error handling
        return ToolReturn(
            return_value=ScreenshotResult(
                status="error",
                url=session.current_url,
                segments_count=0,
                error_message=str(e),
            ).model_dump(),
            content=[],  # No images on error
        )


async def take_element_screenshot(
    selector: str,
    img_format: ImageMediaType = "image/png",
) -> ToolReturn:
    """Capture screenshot of a specific element.

    Args:
        selector: CSS selector for the element
        img_format: Image format (default: "image/png")

    Returns:
        ToolReturn with:
        - return_value: ElementScreenshotResult
        - content: Image segment(s)
    """
    session = get_browser_session()

    try:
        # Enable DOM domain
        await session.cdp_client.send.DOM.enable(session_id=session.page)

        # Get document
        doc = await session.cdp_client.send.DOM.getDocument(session_id=session.page)
        root_node_id = doc["root"]["nodeId"]

        # Query selector
        result = await session.cdp_client.send.DOM.querySelector(
            params={
                "nodeId": root_node_id,
                "selector": selector,
            },
            session_id=session.page,
        )

        node_id = result.get("nodeId")
        if not node_id or node_id == 0:
            return ToolReturn(
                return_value=ElementScreenshotResult(
                    status="not_found",
                    selector=selector,
                    segments_count=0,
                    error_message=f"Element not found: {selector}",
                ).model_dump(),
                content=[],
            )

        # Get element box model
        box_result = await session.cdp_client.send.DOM.getBoxModel(params={"nodeId": node_id}, session_id=session.page)
        border = box_result["model"]["border"]

        # Calculate bounding box (border quad: [x1,y1, x2,y2, x3,y3, x4,y4])
        x = min(border[0], border[2], border[4], border[6])
        y = min(border[1], border[3], border[5], border[7])
        width = max(border[0], border[2], border[4], border[6]) - x
        height = max(border[1], border[3], border[5], border[7]) - y

        element_info = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

        # Capture with clip
        format_suffix = img_format.split("/")[1] if "/" in img_format else img_format
        screenshot_result = await session.cdp_client.send.Page.captureScreenshot(
            params={
                "format": format_suffix,
                "clip": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "scale": 1,
                },
            },
            session_id=session.page,
        )

        screenshot_data = screenshot_result["data"]
        image_bytes = base64.b64decode(screenshot_data)
        segments = split_image_data(
            image_bytes=image_bytes,
            max_height=4096,
            media_type=img_format,
        )

        # Element screenshots should be small, but still limit
        if len(segments) > 20:
            segments = segments[:20]

        return ToolReturn(
            return_value=ElementScreenshotResult(
                status="success",
                selector=selector,
                segments_count=len(segments),
                element_info=element_info,
            ).model_dump(),
            content=segments,
        )

    except Exception as e:
        return ToolReturn(
            return_value=ElementScreenshotResult(
                status="error",
                selector=selector,
                segments_count=0,
                error_message=str(e),
            ).model_dump(),
            content=[],
        )


async def get_viewport_info() -> dict[str, int]:
    """Get current viewport dimensions.

    Returns:
        Dictionary with width and height
    """
    session = get_browser_session()
    return session.viewport.copy()
