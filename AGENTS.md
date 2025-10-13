# pai-browser-use Project Documentation

## Project Overview

Pydantic AI Toolsets for browser automation using Chrome DevTools Protocol (CDP).

## Architecture

### Core Components

1. **BrowserSession** (`_session.py`)

   - Manages CDP client and session state
   - Stores page session_id (CDP session identifier)
   - Exposes `cdp_client` for direct CDP API access with type hints
   - Maintains navigation history and viewport info

1. **Tool Building Infrastructure** (`_tools.py`)

   - Context-based session injection using `ContextVar`
   - `get_browser_session()` retrieves current session in tool functions
   - `build_tool()` wraps functions to inject session transparently

1. **BrowserUseToolset** (`toolset.py`)

   - Pydantic AI toolset integration
   - Manages CDP client lifecycle
   - Creates browser target/page on initialization
   - Rebuilds tools with active session

1. **Tool Categories** (`tools/`)

   - **Navigation**: URL navigation, history, reload
   - **State**: Page info, content, screenshots (with multi-modal support)
   - **Interaction**: Click, type, JavaScript execution, scrolling
   - **Query**: Element finding and inspection

### CDP Integration

- Uses `cdp-use` library for CDP communication
- Direct API access via `session.cdp_client.send.{Domain}.{method}()` for full type hints
- Page reference is CDP `session_id` (string), not a page object
- All CDP calls include `session_id=session.page` parameter
- Supports reusing existing page targets when available

### Multi-Modal Support

**Screenshot Tools** return `ToolReturn` with:

- `return_value`: Structured metadata (ScreenshotResult)
- `content`: List of `BinaryContent` (image segments)

**Image Segmentation**:

- Long screenshots automatically split (max 4096px per segment)
- Maximum 20 segments returned per screenshot
- Uses PIL for image processing

### Tool Function Pattern

```python
async def tool_function(param: type) -> dict | ToolReturn:
    session = get_browser_session()  # Get injected session

    # Enable CDP domains as needed (with type hints!)
    await session.cdp_client.send.Page.enable(session_id=session.page)
    await session.cdp_client.send.DOM.enable(session_id=session.page)

    # Perform CDP operations (enjoy autocomplete and type checking)
    result = await session.cdp_client.send.Page.navigate(
        params={"url": url},
        session_id=session.page
    )

    # Update session state
    session.current_url = url

    # Return structured result
    return SomeResult(status="success", ...).model_dump()
```

### Testing Strategy

- Tests use `build_tool()` to create testable tool instances
- Tools can be invoked independently via `tool.function_schema.call()`
- Docker-based Chrome container for isolated testing (via `conftest.py`)
- Function-style test organization

## Key Design Decisions

1. **CDP Session ID as Page Reference**: Due to `cdp-use` architecture, we use session_id strings instead of page objects
1. **Context-Based Injection**: Clean tool signatures without explicit session parameters
1. **Multi-Modal Screenshots**: Separate return_value (metadata) from content (images)
1. **Automatic Image Splitting**: Handle long pages transparently for LLM compatibility
1. **Page Reuse Strategy**: When initializing, reuse existing page targets if available, otherwise create new ones
1. **Direct CDP API Access**: Tools use `session.cdp_client.send.{Domain}.{method}()` directly to leverage full type hints and autocomplete from cdp-use library

## Development Guidelines

1. **Adding New Tools**:

   - Create tool function in appropriate `tools/*.py` file
   - Add to `tools/__init__.py` ALL_TOOLS list
   - Use `get_browser_session()` to access session
   - Return structured Pydantic models (converted to dict)

1. **CDP Commands**:

   - Always enable required domains before use
   - Use `await session.cdp_client.send.{Domain}.{method}()` directly for type hints
   - Always pass `session_id=session.page` parameter
   - Handle exceptions gracefully with error status
   - Example: `await session.cdp_client.send.Page.navigate(params={"url": url}, session_id=session.page)`

1. **State Management**:

   - Update `session.current_url`, `session.current_title` after navigation
   - Append to `session.navigation_history` when appropriate
   - Use session cache for performance when applicable

## Dependencies

- `cdp-use`: CDP client library
- `pydantic-ai`: Agent framework with toolset support
- `pillow`: Image processing for screenshot splitting
- `httpx`: HTTP client for CDP endpoint discovery

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=pai_browser_use
```

## Example Usage

```python
from pydantic_ai import Agent
from pai_browser_use import BrowserUseToolset

agent = Agent(
    model="anthropic:claude-sonnet-4-5",
    system_prompt="You are a browser automation assistant.",
    toolsets=[
        BrowserUseToolset(cdp_url="http://localhost:9222/json/version"),
    ],
)

result = await agent.run("Navigate to example.com and take a screenshot")
```
