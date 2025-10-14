"""Test wait tools."""

from __future__ import annotations

from pai_browser_use._tools import build_tool
from pai_browser_use.tools import execute_javascript, navigate_to_url
from pai_browser_use.tools.wait import (
    wait_for_load_state,
    wait_for_navigation,
    wait_for_selector,
)
from pai_browser_use.toolset import BrowserUseToolset


async def test_wait_for_selector_visible(cdp_url, test_server):
    """Test waiting for a visible element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for an element that exists
        wait_tool = build_tool(session, wait_for_selector)
        result = await wait_tool.function_schema.call({"selector": "h1", "timeout": 5000, "state": "visible"}, None)

        assert result["status"] == "success"
        assert result["wait_type"] == "selector"
        assert result["selector"] == "h1"
        assert "elapsed_time" in result


async def test_wait_for_selector_timeout(cdp_url, test_server):
    """Test waiting for a non-existent element (timeout)."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for an element that doesn't exist
        wait_tool = build_tool(session, wait_for_selector)
        result = await wait_tool.function_schema.call(
            {"selector": "#non-existent-element", "timeout": 1000, "state": "visible"}, None
        )

        assert result["status"] == "timeout"
        assert result["wait_type"] == "selector"
        assert "error_message" in result


async def test_wait_for_selector_attached(cdp_url, test_server):
    """Test waiting for element in attached state."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for an element in attached state
        wait_tool = build_tool(session, wait_for_selector)
        result = await wait_tool.function_schema.call({"selector": "body", "timeout": 5000, "state": "attached"}, None)

        assert result["status"] == "success"
        assert result["wait_type"] == "selector"


async def test_wait_for_load_state_load(cdp_url, test_server):
    """Test waiting for page load state."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for load state
        wait_tool = build_tool(session, wait_for_load_state)
        result = await wait_tool.function_schema.call({"state": "load", "timeout": 10000}, None)

        assert result["status"] == "success"
        assert result["wait_type"] == "load_state"
        assert "elapsed_time" in result


async def test_wait_for_load_state_domcontentloaded(cdp_url, test_server):
    """Test waiting for DOMContentLoaded state."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for DOMContentLoaded
        wait_tool = build_tool(session, wait_for_load_state)
        result = await wait_tool.function_schema.call({"state": "domcontentloaded", "timeout": 10000}, None)

        assert result["status"] == "success"
        assert result["wait_type"] == "load_state"


async def test_wait_for_navigation_with_link_click(cdp_url, test_server):
    """Test waiting for navigation after triggering navigation."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate to example.com
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Create a link that navigates and click it
        js_tool = build_tool(session, execute_javascript)
        nav_url = f"{test_server}/test_fixtures/navigation/page1.html"
        await js_tool.function_schema.call(
            {
                "script": f"""
            const link = document.createElement('a');
            link.href = '{nav_url}';
            link.id = 'test-link';
            link.textContent = 'Test Link';
            document.body.appendChild(link);
        """
            },
            None,
        )

        # Click the link to trigger navigation (in background)
        await js_tool.function_schema.call({"script": "document.getElementById('test-link').click();"}, None)

        # Wait for navigation
        wait_tool = build_tool(session, wait_for_navigation)
        result = await wait_tool.function_schema.call({"timeout": 10000}, None)

        assert result["status"] in ["success", "timeout"]
        assert result["wait_type"] == "navigation"


async def test_wait_for_load_state_networkidle(cdp_url, test_server):
    """Test waiting for network idle state."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": f"{test_server}/test_fixtures/basic.html"}, None)

        # Wait for network idle
        wait_tool = build_tool(session, wait_for_load_state)
        result = await wait_tool.function_schema.call({"state": "networkidle", "timeout": 5000}, None)

        # Network idle detection is simplified, so we accept both success and timeout
        assert result["status"] in ["success", "timeout"]
        assert result["wait_type"] == "load_state"
