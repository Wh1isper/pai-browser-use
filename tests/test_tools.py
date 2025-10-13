"""Test browser automation tools."""

from __future__ import annotations

import io

from PIL import Image
from pydantic_ai import BinaryContent
from pydantic_ai.messages import ToolReturn

from pai_browser_use._tools import build_tool
from pai_browser_use.tools import (
    click_element,
    find_elements,
    get_page_content,
    get_page_info,
    navigate_to_url,
    take_screenshot,
)
from pai_browser_use.toolset import BrowserUseToolset


async def test_navigate_to_url(cdp_url):
    """Test navigation to a URL."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Build and call tool
        tool = build_tool(session, navigate_to_url)
        result = await tool.function_schema.call({"url": "https://example.com"}, None)

        # Verify result structure
        assert result["status"] == "success"
        assert "example.com" in result["url"]
        assert result["title"] != ""

        # Verify session state updated
        assert "example.com" in session.current_url
        assert session.current_title != ""
        assert len(session.navigation_history) > 0


async def test_get_page_info(cdp_url):
    """Test getting page information."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first using tool
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Get page info
        tool = build_tool(session, get_page_info)
        result = await tool.function_schema.call({}, None)

        # Verify structure
        assert "url" in result
        assert "title" in result
        assert "ready_state" in result
        assert "viewport" in result
        assert "example.com" in result["url"]


async def test_take_screenshot(cdp_url):
    """Test screenshot capture with ToolReturn structure."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first using tool
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Take screenshot
        tool = build_tool(session, take_screenshot)
        result = await tool.function_schema.call({"full_page": False}, None)

        # Verify it's a ToolReturn
        assert isinstance(result, ToolReturn)

        # Verify return_value structure
        assert "status" in result.return_value
        assert result.return_value["status"] == "success"
        assert "url" in result.return_value
        assert "segments_count" in result.return_value
        assert result.return_value["segments_count"] > 0

        # Verify content structure (multi-modal)
        assert isinstance(result.content, list)
        assert len(result.content) > 0
        assert len(result.content) <= 20

        # All content items should be BinaryContent
        for item in result.content:
            assert isinstance(item, BinaryContent)
            assert item.media_type == "image/png"

        # Verify image data is valid
        first_image = result.content[0]
        img = Image.open(io.BytesIO(first_image.data))
        assert img.size[0] > 0
        assert img.size[1] > 0


async def test_get_page_content(cdp_url):
    """Test getting page content."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first using tool
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Get text content
        tool = build_tool(session, get_page_content)
        result = await tool.function_schema.call({"content_format": "text"}, None)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Example" in result or "example" in result.lower()


async def test_find_elements(cdp_url):
    """Test finding elements on page."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first using tool
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Find h1 elements
        tool = build_tool(session, find_elements)
        result = await tool.function_schema.call({"selector": "h1", "limit": 10}, None)

        assert result["status"] == "success"
        assert result["count"] >= 0
        assert "elements" in result

        if result["count"] > 0:
            element = result["elements"][0]
            assert "tag_name" in element
            assert element["tag_name"] == "h1"
            assert "text" in element


async def test_click_element(cdp_url):
    """Test clicking an element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first using tool
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to click a link (if exists)
        tool = build_tool(session, click_element)
        result = await tool.function_schema.call({"selector": "a"}, None)

        # Result should indicate success or not_found
        assert result["status"] in ["success", "not_found", "error"]
        assert "selector" in result


async def test_toolset_context_manager(cdp_url):
    """Test BrowserUseToolset as context manager."""
    async with BrowserUseToolset(cdp_url) as toolset:
        assert toolset._cdp_client is not None
        assert toolset._browser_session is not None
        assert toolset._browser_session.page is not None
        assert len(toolset._tools) > 0

    # After exit, should be cleaned up
    assert toolset._cdp_client is None
