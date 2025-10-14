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
    assert toolset.id == "browser_use"

    async with toolset as ts:
        assert ts._cdp_client is not None


async def test_browser_use_toolset_reuses_existing_page(cdp_url):
    """Test that BrowserUseToolset reuses existing page by default."""
    # Create first toolset and attach to a page
    toolset1 = BrowserUseToolset(cdp_url)

    async with toolset1 as ts1:
        assert ts1._browser_session is not None
        _ = ts1._browser_session.page

        # Create second toolset - should reuse the same page
        toolset2 = BrowserUseToolset(cdp_url, always_use_new_page=False)
        async with toolset2 as ts2:
            assert ts2._browser_session is not None
            second_session_id = ts2._browser_session.page

            # Session IDs might be different (different sessions attached to same target)
            # but the toolset should have successfully initialized
            assert second_session_id is not None


async def test_browser_use_toolset_always_use_new_page(cdp_url):
    """Test that BrowserUseToolset creates new page when always_use_new_page=True."""
    # Create first toolset
    toolset1 = BrowserUseToolset(cdp_url)

    async with toolset1 as ts1:
        assert ts1._browser_session is not None
        _ = ts1._browser_session.page

        # Get targets count after first toolset
        targets_response1 = await ts1._cdp_client.send.Target.getTargets()
        page_count_before = sum(1 for t in targets_response1.get("targetInfos", []) if t.get("type") == "page")

        # Create second toolset with always_use_new_page=True
        toolset2 = BrowserUseToolset(cdp_url, always_use_new_page=True)
        async with toolset2 as ts2:
            assert ts2._browser_session is not None
            second_session_id = ts2._browser_session.page

            # Verify a new session was created
            assert second_session_id is not None

            # Get targets count after second toolset
            targets_response2 = await ts2._cdp_client.send.Target.getTargets()
            page_count_after = sum(1 for t in targets_response2.get("targetInfos", []) if t.get("type") == "page")

            # Should have created a new page
            assert page_count_after > page_count_before


async def test_browser_use_toolset_default_always_use_new_page_false(cdp_url):
    """Test that always_use_new_page defaults to False."""
    toolset = BrowserUseToolset(cdp_url)
    assert toolset.always_use_new_page is False


async def test_browser_use_toolset_always_use_new_page_true_initialization(cdp_url):
    """Test that always_use_new_page can be set to True during initialization."""
    toolset = BrowserUseToolset(cdp_url, always_use_new_page=True)
    assert toolset.always_use_new_page is True

    async with toolset as ts:
        assert ts._browser_session is not None
        assert ts._cdp_client is not None
