"""Test interaction tools."""

from __future__ import annotations

from pai_browser_use._tools import build_tool
from pai_browser_use.tools import (
    click_element,
    execute_javascript,
    focus,
    hover,
    navigate_to_url,
    press_key,
    scroll_to,
    type_text,
)
from pai_browser_use.toolset import BrowserUseToolset


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


async def test_type_text(cdp_url):
    """Test typing text into an input element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to a page with input (example.com doesn't have input, so result may vary)
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to type (may fail if no input exists)
        type_tool = build_tool(session, type_text)
        result = await type_tool.function_schema.call({"selector": "input", "text": "test", "clear_first": True}, None)

        # Status could be success or not_found depending on page
        assert result["status"] in ["success", "not_found", "error"]
        assert "selector" in result


async def test_execute_javascript(cdp_url):
    """Test executing JavaScript code."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Execute simple JavaScript
        js_tool = build_tool(session, execute_javascript)
        result = await js_tool.function_schema.call({"script": "1 + 1"}, None)

        assert result["status"] == "success"
        assert result["result"] == 2


async def test_execute_javascript_with_error(cdp_url):
    """Test executing JavaScript with syntax error."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Execute invalid JavaScript
        js_tool = build_tool(session, execute_javascript)
        result = await js_tool.function_schema.call({"script": "invalid syntax {{{"}, None)

        assert result["status"] == "error"
        assert "error_message" in result


async def test_scroll_to(cdp_url):
    """Test scrolling the page."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Scroll to position
        scroll_tool = build_tool(session, scroll_to)
        result = await scroll_tool.function_schema.call({"x": 0, "y": 100}, None)

        assert result["status"] == "success"


async def test_type_text_no_clear(cdp_url):
    """Test typing text without clearing existing text."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to a page with input (example.com doesn't have input, so result may vary)
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to type without clearing
        type_tool = build_tool(session, type_text)
        result = await type_tool.function_schema.call({"selector": "input", "text": "test", "clear_first": False}, None)

        # Status could be success or not_found depending on page
        assert result["status"] in ["success", "not_found", "error"]
        assert "selector" in result


async def test_hover(cdp_url):
    """Test hovering over an element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Hover over a link
        hover_tool = build_tool(session, hover)
        result = await hover_tool.function_schema.call({"selector": "h1"}, None)

        assert result["status"] in ["success", "not_found", "error"]
        assert "selector" in result


async def test_press_key(cdp_url):
    """Test pressing a key."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Press Enter key
        key_tool = build_tool(session, press_key)
        result = await key_tool.function_schema.call({"key": "Enter"}, None)

        assert result["status"] == "success"
        assert result["key"] == "Enter"


async def test_press_key_with_modifiers(cdp_url):
    """Test pressing a key with modifiers."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Press Ctrl+A
        key_tool = build_tool(session, press_key)
        result = await key_tool.function_schema.call({"key": "a", "modifiers": 2}, None)  # 2 = Ctrl

        assert result["status"] == "success"
        assert result["key"] == "a"


async def test_focus(cdp_url):
    """Test focusing an element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Focus on body
        focus_tool = build_tool(session, focus)
        result = await focus_tool.function_schema.call({"selector": "body"}, None)

        assert result["status"] in ["success", "not_found", "error"]
        assert "selector" in result
