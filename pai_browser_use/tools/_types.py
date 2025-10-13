"""Type definitions for tool return values."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


# Navigation results
class NavigationResult(BaseModel):
    """Navigation operation result."""

    status: Literal["success", "error", "timeout"]
    url: str
    title: str = ""
    error_message: str | None = None


# State inspection results
class PageInfo(BaseModel):
    """Current page information."""

    url: str
    title: str
    ready_state: str
    viewport: dict[str, int]


class ScreenshotResult(BaseModel):
    """Screenshot operation result."""

    status: Literal["success", "error"]
    url: str
    segments_count: int
    truncated: bool = False
    error_message: str | None = None
    format: str = "png"
    full_page: bool = False


class ElementScreenshotResult(BaseModel):
    """Element screenshot result."""

    status: Literal["success", "error", "not_found"]
    selector: str
    segments_count: int
    element_info: dict[str, Any] | None = None
    error_message: str | None = None


# Interaction results
class ClickResult(BaseModel):
    """Click operation result."""

    status: Literal["success", "error", "not_found"]
    selector: str
    element_info: dict[str, Any] | None = None
    error_message: str | None = None


class TypeTextResult(BaseModel):
    """Type text operation result."""

    status: Literal["success", "error", "not_found"]
    selector: str
    text: str
    error_message: str | None = None


class ExecuteScriptResult(BaseModel):
    """Execute JavaScript result."""

    status: Literal["success", "error"]
    result: Any = None
    error_message: str | None = None


# Query results
class ElementInfo(BaseModel):
    """Element information."""

    selector: str
    tag_name: str
    text: str
    attributes: dict[str, str]
    bounding_box: dict[str, float] | None = None


class FindElementsResult(BaseModel):
    """Find elements result."""

    status: Literal["success", "error"]
    selector: str
    count: int
    elements: list[ElementInfo] = []
    error_message: str | None = None
