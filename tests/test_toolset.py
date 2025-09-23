from pai_browser_use.toolset import BrowserUseToolset, get_cdp_websocket_url


def test_get_cdp_websocket_url_with_ws_url():
    """Test that ws:// URLs are returned as-is."""
    ws_url = "ws://127.0.0.1:9222/devtools/browser/abc123"
    result = get_cdp_websocket_url(ws_url)
    assert result == ws_url


def test_get_cdp_websocket_url_with_wss_url():
    """Test that wss:// URLs are returned as-is."""
    wss_url = "wss://127.0.0.1:9222/devtools/browser/abc123"
    result = get_cdp_websocket_url(wss_url)
    assert result == wss_url


async def test_browser_use_toolset_async_context(cdp_url):
    """Test that BrowserUseToolset can be used as an async context manager."""
    # This test would require a running CDP endpoint or mock
    # For now, just test that the class can be instantiated
    toolset = BrowserUseToolset(cdp_url)
    assert toolset.id == "browser-use"

    async with toolset as ts:
        assert ts._cdp_client is not None
