"""Dialog handling tools for browser control."""

from __future__ import annotations

import asyncio
from typing import Any

from pai_browser_use._logger import logger
from pai_browser_use._tools import get_browser_session
from pai_browser_use.tools._types import DialogResult


async def handle_dialog(
    accept: bool = True,
    prompt_text: str | None = None,
    timeout: int = 5000,
) -> dict[str, Any]:
    """Handle JavaScript dialog (alert, confirm, prompt).

    This function waits for a dialog to appear and handles it.

    Args:
        accept: Whether to accept (True) or dismiss (False) the dialog
        prompt_text: Text to enter for prompt dialogs (optional)
        timeout: Maximum time to wait for dialog in milliseconds (default: 5000)

    Returns:
        DialogResult dictionary
    """
    logger.info(f"Waiting for dialog (accept={accept}, timeout={timeout}ms)")
    session = get_browser_session()

    try:
        # Enable Page domain
        await session.cdp_client.send.Page.enable(session_id=session.page)

        # Wait for dialog to appear (simplified approach)
        timeout_seconds = timeout / 1000
        poll_interval = 0.1
        elapsed = 0.0

        # First, try to handle any existing dialog immediately
        try:
            await session.cdp_client.send.Page.handleJavaScriptDialog(
                params={
                    "accept": accept,
                    "promptText": prompt_text if prompt_text else "",
                },
                session_id=session.page,
            )
            logger.info("Dialog handled successfully")
            return DialogResult(
                status="success",
                accepted=accept,
                prompt_text=prompt_text,
            ).model_dump()
        except Exception as e:
            # No dialog present, will wait for one
            logger.debug(f"No existing dialog found: {e}")

        # Wait for dialog to appear by polling
        while elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            try:
                # Try to handle dialog
                await session.cdp_client.send.Page.handleJavaScriptDialog(
                    params={
                        "accept": accept,
                        "promptText": prompt_text if prompt_text else "",
                    },
                    session_id=session.page,
                )
                logger.info(f"Dialog detected and handled after {elapsed:.2f}s")
                return DialogResult(
                    status="success",
                    accepted=accept,
                    prompt_text=prompt_text,
                ).model_dump()
            except Exception as e:
                # Dialog not yet present
                logger.debug(f"Dialog not yet present (elapsed: {elapsed:.2f}s): {e}")
                continue

        # Timeout reached
        logger.warning(f"No dialog detected within {timeout}ms")
        return DialogResult(
            status="no_dialog",
            error_message=f"No dialog detected within {timeout}ms",
        ).model_dump()

    except Exception as e:  # pragma: no cover
        logger.error(f"Error handling dialog: {e}")
        return DialogResult(
            status="error",
            error_message=str(e),
        ).model_dump()


async def dismiss_dialog(timeout: int = 5000) -> dict[str, Any]:
    """Dismiss/cancel a JavaScript dialog.

    Convenience function that calls handle_dialog with accept=False.

    Args:
        timeout: Maximum time to wait for dialog in milliseconds (default: 5000)

    Returns:
        DialogResult dictionary
    """
    return await handle_dialog(accept=False, timeout=timeout)


async def accept_dialog(prompt_text: str | None = None, timeout: int = 5000) -> dict[str, Any]:
    """Accept/confirm a JavaScript dialog.

    Convenience function that calls handle_dialog with accept=True.

    Args:
        prompt_text: Text to enter for prompt dialogs (optional)
        timeout: Maximum time to wait for dialog in milliseconds (default: 5000)

    Returns:
        DialogResult dictionary
    """
    return await handle_dialog(accept=True, prompt_text=prompt_text, timeout=timeout)
