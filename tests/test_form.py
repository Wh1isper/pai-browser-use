"""Test form operation tools."""

from __future__ import annotations

from pai_browser_use._tools import build_tool
from pai_browser_use.tools import execute_javascript, navigate_to_url
from pai_browser_use.tools.form import check, select_option, uncheck, upload_file
from pai_browser_use.toolset import BrowserUseToolset


async def test_select_option_by_value(cdp_url):
    """Test selecting option by value."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a select element
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const select = document.createElement('select');
            select.id = 'test-select';
            const opt1 = document.createElement('option');
            opt1.value = 'value1';
            opt1.text = 'Option 1';
            const opt2 = document.createElement('option');
            opt2.value = 'value2';
            opt2.text = 'Option 2';
            select.appendChild(opt1);
            select.appendChild(opt2);
            document.body.appendChild(select);
        """
            },
            None,
        )

        # Select by value
        select_tool = build_tool(session, select_option)
        result = await select_tool.function_schema.call({"selector": "#test-select", "value": "value2"}, None)

        assert result["status"] == "success"
        assert result["value"] == "value2"


async def test_select_option_by_label(cdp_url):
    """Test selecting option by label."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a select element
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const select = document.createElement('select');
            select.id = 'test-select-label';
            const opt1 = document.createElement('option');
            opt1.value = 'val1';
            opt1.text = 'First Option';
            const opt2 = document.createElement('option');
            opt2.value = 'val2';
            opt2.text = 'Second Option';
            select.appendChild(opt1);
            select.appendChild(opt2);
            document.body.appendChild(select);
        """
            },
            None,
        )

        # Select by label
        select_tool = build_tool(session, select_option)
        result = await select_tool.function_schema.call(
            {"selector": "#test-select-label", "label": "Second Option"}, None
        )

        assert result["status"] == "success"
        assert result["label"] == "Second Option"


async def test_select_option_by_index(cdp_url):
    """Test selecting option by index."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a select element
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const select = document.createElement('select');
            select.id = 'test-select-index';
            const opt1 = document.createElement('option');
            opt1.value = 'val1';
            opt1.text = 'Option 1';
            const opt2 = document.createElement('option');
            opt2.value = 'val2';
            opt2.text = 'Option 2';
            select.appendChild(opt1);
            select.appendChild(opt2);
            document.body.appendChild(select);
        """
            },
            None,
        )

        # Select by index
        select_tool = build_tool(session, select_option)
        result = await select_tool.function_schema.call({"selector": "#test-select-index", "index": 1}, None)

        assert result["status"] == "success"
        assert result["index"] == 1


async def test_check_checkbox(cdp_url):
    """Test checking a checkbox."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a checkbox
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = 'test-checkbox';
            document.body.appendChild(checkbox);
        """
            },
            None,
        )

        # Check the checkbox
        check_tool = build_tool(session, check)
        result = await check_tool.function_schema.call({"selector": "#test-checkbox"}, None)

        assert result["status"] == "success"
        assert result["checked"] is True


async def test_uncheck_checkbox(cdp_url):
    """Test unchecking a checkbox."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a checked checkbox
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = 'test-checkbox-uncheck';
            checkbox.checked = true;
            document.body.appendChild(checkbox);
        """
            },
            None,
        )

        # Uncheck the checkbox
        uncheck_tool = build_tool(session, uncheck)
        result = await uncheck_tool.function_schema.call({"selector": "#test-checkbox-uncheck"}, None)

        assert result["status"] == "success"
        assert result["checked"] is False


async def test_check_radio(cdp_url):
    """Test checking a radio button."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a radio button
        js_tool = build_tool(session, execute_javascript)
        await js_tool.function_schema.call(
            {
                "script": """
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.id = 'test-radio';
            radio.name = 'test-group';
            document.body.appendChild(radio);
        """
            },
            None,
        )

        # Check the radio button
        check_tool = build_tool(session, check)
        result = await check_tool.function_schema.call({"selector": "#test-radio"}, None)

        assert result["status"] == "success"
        assert result["checked"] is True


async def test_upload_file_not_found(cdp_url, tmp_path):
    """Test file upload with non-existent element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Create a temporary file using pytest's tmp_path fixture
        temp_file = tmp_path / "test_file.txt"
        temp_file.write_text("test content")

        upload_tool = build_tool(session, upload_file)
        result = await upload_tool.function_schema.call(
            {"selector": "#non-existent-file-input", "file_paths": [str(temp_file)]}, None
        )

        assert result["status"] == "not_found"


async def test_select_option_not_found(cdp_url):
    """Test selecting option on non-existent element."""
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session

        # Navigate first
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call({"url": "https://example.com"}, None)

        # Try to select on non-existent element
        select_tool = build_tool(session, select_option)
        result = await select_tool.function_schema.call({"selector": "#non-existent-select", "value": "test"}, None)

        assert result["status"] == "not_found"
