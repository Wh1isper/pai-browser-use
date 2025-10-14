"""Browser automation tools."""

from pai_browser_use.tools.interaction import (
    click_element,
    execute_javascript,
    scroll_to,
    type_text,
)
from pai_browser_use.tools.navigation import (
    go_back,
    go_forward,
    navigate_to_url,
    reload_page,
)
from pai_browser_use.tools.query import (
    find_elements,
    get_element_attributes,
    get_element_text,
)
from pai_browser_use.tools.state import (
    get_page_content,
    get_page_info,
    get_viewport_info,
    take_element_screenshot,
    take_screenshot,
)

# Export all tools for registration
ALL_TOOLS = [
    # Navigation
    navigate_to_url,
    go_back,
    go_forward,
    reload_page,
    # State inspection
    get_page_info,
    get_page_content,
    take_screenshot,
    take_element_screenshot,
    get_viewport_info,
    # Interaction
    click_element,
    type_text,
    execute_javascript,
    scroll_to,
    # Query
    find_elements,
    get_element_text,
    get_element_attributes,
]

__all__ = [
    "ALL_TOOLS",
    "click_element",
    "execute_javascript",
    "find_elements",
    "get_element_attributes",
    "get_element_text",
    "get_page_content",
    "get_page_info",
    "get_viewport_info",
    "go_back",
    "go_forward",
    "navigate_to_url",
    "reload_page",
    "scroll_to",
    "take_element_screenshot",
    "take_screenshot",
    "type_text",
]
