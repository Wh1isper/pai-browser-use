"""Test navigation tools."""

from __future__ import annotations

from pai_browser_use._tools import build_tool
from pai_browser_use.tools import go_back, go_forward, navigate_to_url, reload_page
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


async def test_go_back(cdp_url):
    """Test going back in navigation history."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to first page
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Navigate to second page
        await nav_tool.function_schema.call({"url": "https://example.org"}, None)

        # Go back
        back_tool = build_tool(session, go_back)
        result = await back_tool.function_schema.call({}, None)

        assert result["status"] == "success"
        assert "example.com" in result["url"]


async def test_go_forward(cdp_url):
    """Test going forward in navigation history."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to pages and go back
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)
        await nav_tool.function_schema.call({"url": "https://example.org"}, None)

        back_tool = build_tool(session, go_back)
        await back_tool.function_schema.call({}, None)

        # Go forward
        forward_tool = build_tool(session, go_forward)
        result = await forward_tool.function_schema.call({}, None)

        assert result["status"] == "success"
        assert "example.org" in result["url"]


async def test_reload_page(cdp_url):
    """Test reloading the current page."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Reload page
        reload_tool = build_tool(session, reload_page)
        result = await reload_tool.function_schema.call({"ignore_cache": False}, None)

        assert result["status"] == "success"
        assert "example.com" in result["url"]


async def test_reload_page_ignore_cache(cdp_url):
    """Test reloading page with cache ignored."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        reload_tool = build_tool(session, reload_page)
        result = await reload_tool.function_schema.call({"ignore_cache": True}, None)

        assert result["status"] == "success"


async def test_go_back_no_history(cdp_url):
    """Test going back when already at the first page."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to only one page
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to go back - may succeed (about:blank) or fail depending on browser state
        back_tool = build_tool(session, go_back)
        result = await back_tool.function_schema.call({}, None)

        # Just verify the call completed (success or error both valid)
        assert result["status"] in ["success", "error"]


async def test_go_forward_no_history(cdp_url):
    """Test going forward when already at the last page."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to a page (no forward history)
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to go forward (should fail)
        forward_tool = build_tool(session, go_forward)
        result = await forward_tool.function_schema.call({}, None)

        # Should return error for no next page
        assert result["status"] == "error"
        assert "history" in result.get("error_message", "").lower()
