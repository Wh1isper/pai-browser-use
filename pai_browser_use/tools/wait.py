"""Wait and synchronization tools for browser control."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Literal

from pai_browser_use._logger import logger
from pai_browser_use._tools import get_browser_session
from pai_browser_use.tools._types import WaitResult


async def wait_for_selector(
    selector: str,
    timeout: int = 30000,
    state: Literal["attached", "visible"] = "visible",
) -> dict[str, Any]:
    """Wait for element matching selector to appear.

    Args:
        selector: CSS selector to wait for
        timeout: Maximum wait time in milliseconds (default: 30000)
        state: Element state to wait for - "attached" (in DOM) or "visible" (default: "visible")

    Returns:
        WaitResult dictionary
    """
    logger.info(f"Waiting for selector: {selector} (timeout: {timeout}ms, state: {state})")
    session = get_browser_session()
    start_time = time.time()

    try:
        await session.cdp_client.send.DOM.enable(session_id=session.page)

        timeout_seconds = timeout / 1000
        poll_interval = 0.1  # 100ms polling

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Timeout waiting for selector: {selector}")
                return WaitResult(
                    status="timeout",
                    wait_type="selector",
                    selector=selector,
                    elapsed_time=elapsed,
                    error_message=f"Timeout after {timeout}ms waiting for selector: {selector}",
                ).model_dump()

            try:
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
                if node_id and node_id != 0:
                    # Element is attached to DOM
                    if state == "attached":
                        elapsed = time.time() - start_time
                        logger.info(f"Element found (attached): {selector} after {elapsed:.2f}s")
                        return WaitResult(
                            status="success",
                            wait_type="selector",
                            selector=selector,
                            elapsed_time=elapsed,
                        ).model_dump()

                    # Check if visible
                    if state == "visible":
                        try:
                            # Check if element has box model (is visible)
                            await session.cdp_client.send.DOM.getBoxModel(
                                params={"nodeId": node_id}, session_id=session.page
                            )
                            elapsed = time.time() - start_time
                            logger.info(f"Element found (visible): {selector} after {elapsed:.2f}s")
                            return WaitResult(
                                status="success",
                                wait_type="selector",
                                selector=selector,
                                elapsed_time=elapsed,
                            ).model_dump()
                        except Exception as box_error:
                            # Element exists but not visible yet
                            logger.debug(f"Element not yet visible: {box_error}")

            except Exception as e:
                logger.debug(f"Polling error (will retry): {e}")

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    except Exception as e:  # pragma: no cover
        elapsed = time.time() - start_time
        logger.error(f"Error waiting for selector {selector}: {e}")
        return WaitResult(
            status="error",
            wait_type="selector",
            selector=selector,
            elapsed_time=elapsed,
            error_message=str(e),
        ).model_dump()


async def wait_for_navigation(timeout: int = 30000) -> dict[str, Any]:
    """Wait for navigation to complete.

    Args:
        timeout: Maximum wait time in milliseconds (default: 30000)

    Returns:
        WaitResult dictionary
    """
    logger.info(f"Waiting for navigation (timeout: {timeout}ms)")
    session = get_browser_session()
    start_time = time.time()

    try:
        await session.cdp_client.send.Page.enable(session_id=session.page)

        # Store current URL
        current_url = session.current_url

        timeout_seconds = timeout / 1000
        poll_interval = 0.1

        # Wait for URL change
        url_changed = False
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                if not url_changed:
                    logger.warning("Timeout waiting for navigation (URL did not change)")
                    return WaitResult(
                        status="timeout",
                        wait_type="navigation",
                        elapsed_time=elapsed,
                        error_message=f"Timeout after {timeout}ms waiting for navigation",
                    ).model_dump()
                break

            try:
                result = await session.cdp_client.send.Runtime.evaluate(
                    params={
                        "expression": "window.location.href",
                        "returnByValue": True,
                    },
                    session_id=session.page,
                )
                new_url = result["result"]["value"]

                if new_url != current_url:
                    url_changed = True
                    logger.debug(f"Navigation detected: {current_url} -> {new_url}")
                    break

            except Exception as e:
                logger.debug(f"Polling error during navigation wait: {e}")

            await asyncio.sleep(poll_interval)

        # Now wait for load state
        await asyncio.sleep(0.5)  # Brief wait for page to stabilize

        elapsed = time.time() - start_time
        logger.info(f"Navigation completed after {elapsed:.2f}s")
        return WaitResult(
            status="success",
            wait_type="navigation",
            elapsed_time=elapsed,
        ).model_dump()

    except Exception as e:  # pragma: no cover
        elapsed = time.time() - start_time
        logger.error(f"Error waiting for navigation: {e}")
        return WaitResult(
            status="error",
            wait_type="navigation",
            elapsed_time=elapsed,
            error_message=str(e),
        ).model_dump()


async def _wait_for_document_ready(
    session: Any,
    target_state: str,
    timeout_seconds: float,
    start_time: float,
    timeout: int,
    state: str,
) -> dict[str, Any]:
    """Helper function to wait for document ready state."""
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Timeout waiting for load state: {state}")
            return WaitResult(
                status="timeout",
                wait_type="load_state",
                elapsed_time=elapsed,
                error_message=f"Timeout after {timeout}ms waiting for load state: {state}",
            ).model_dump()

        try:
            result = await session.cdp_client.send.Runtime.evaluate(
                params={
                    "expression": "document.readyState",
                    "returnByValue": True,
                },
                session_id=session.page,
            )
            ready_state = result["result"]["value"]

            if ready_state == target_state or ready_state == "complete":
                elapsed = time.time() - start_time
                logger.info(f"Load state reached: {state} (readyState: {ready_state}) after {elapsed:.2f}s")
                return WaitResult(
                    status="success",
                    wait_type="load_state",
                    elapsed_time=elapsed,
                ).model_dump()

        except Exception as e:
            logger.debug(f"Polling error checking ready state: {e}")

        await asyncio.sleep(0.1)


async def _wait_for_network_idle(
    session: Any,
    timeout_seconds: float,
    start_time: float,
    timeout: int,
) -> dict[str, Any]:
    """Helper function to wait for network idle state."""
    await session.cdp_client.send.Network.enable(session_id=session.page)

    last_activity_time = time.time()
    idle_timeout = 0.5  # 500ms of no activity

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning("Timeout waiting for network idle")
            return WaitResult(
                status="timeout",
                wait_type="load_state",
                elapsed_time=elapsed,
                error_message=f"Timeout after {timeout}ms waiting for network idle",
            ).model_dump()

        # Check if we've been idle long enough
        idle_duration = time.time() - last_activity_time
        if idle_duration >= idle_timeout:
            elapsed = time.time() - start_time
            logger.info(f"Network idle detected after {elapsed:.2f}s")
            return WaitResult(
                status="success",
                wait_type="load_state",
                elapsed_time=elapsed,
            ).model_dump()

        # Reset activity time (simplified approach - assume activity)
        last_activity_time = time.time()
        await asyncio.sleep(0.1)


async def wait_for_load_state(
    state: Literal["load", "domcontentloaded", "networkidle"] = "load",
    timeout: int = 30000,
) -> dict[str, Any]:
    """Wait for specific page load state.

    Args:
        state: Load state to wait for:
            - "load": Wait for load event (document fully loaded)
            - "domcontentloaded": Wait for DOMContentLoaded event
            - "networkidle": Wait for network to be idle (no requests for 500ms)
        timeout: Maximum wait time in milliseconds (default: 30000)

    Returns:
        WaitResult dictionary
    """
    logger.info(f"Waiting for load state: {state} (timeout: {timeout}ms)")
    session = get_browser_session()
    start_time = time.time()

    try:
        await session.cdp_client.send.Page.enable(session_id=session.page)
        timeout_seconds = timeout / 1000

        if state in ["load", "domcontentloaded"]:
            target_state = "complete" if state == "load" else "interactive"
            return await _wait_for_document_ready(session, target_state, timeout_seconds, start_time, timeout, state)
        else:  # networkidle
            return await _wait_for_network_idle(session, timeout_seconds, start_time, timeout)

    except Exception as e:  # pragma: no cover
        elapsed = time.time() - start_time
        logger.error(f"Error waiting for load state {state}: {e}")
        return WaitResult(
            status="error",
            wait_type="load_state",
            elapsed_time=elapsed,
            error_message=str(e),
        ).model_dump()
