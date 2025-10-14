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
   - `build_tool()` wraps functions to inject session transparently and applies optional prefix to tool names

1. **BrowserUseToolset** (`toolset.py`)

   - Pydantic AI toolset integration
   - Manages CDP client lifecycle
   - Creates browser target/page on initialization
   - Rebuilds tools with active session

1. **Tool Categories** (`tools/`)

   - **Navigation**: URL navigation, history, reload
   - **State**: Page info, content, screenshots (with multi-modal support)
   - **Interaction**: Click, type, hover, focus, key press, JavaScript execution, scrolling
   - **Query**: Element finding and inspection
   - **Wait**: Element waiting, navigation waiting, load state waiting
   - **Form**: Select options, checkbox/radio operations, file upload
   - **Dialog**: JavaScript dialog handling (alert, confirm, prompt)
   - **Validation**: Element visibility, enabled state, checked state

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
- **Nginx container serves local test HTML files** (eliminates external dependencies)
- **Docker network architecture**: Chrome and Nginx containers communicate via shared network
- Test fixtures located in `tests/test_fixtures/` directory
- Function-style test organization

## Key Design Decisions

1. **CDP Session ID as Page Reference**: Due to `cdp-use` architecture, we use session_id strings instead of page objects
1. **Context-Based Injection**: Clean tool signatures without explicit session parameters
1. **Multi-Modal Screenshots**: Separate return_value (metadata) from content (images)
1. **Automatic Image Splitting**: Handle long pages transparently for LLM compatibility
1. **Page Reuse Strategy**: When initializing, reuse existing page targets if available, otherwise create new ones
1. **Direct CDP API Access**: Tools use `session.cdp_client.send.{Domain}.{method}()` directly to leverage full type hints and autocomplete from cdp-use library
1. **Intelligent Wait Strategy**: Navigation tools use `asyncio.timeout` with `wait_for_load_state` for reliable page load detection instead of fixed `asyncio.sleep` delays

## Development Guidelines

### Code Quality Standards

1. **Import Organization**:

   - All imports MUST be at the top of the file
   - Never use imports inside functions or methods
   - Follow standard import ordering: stdlib, third-party, local

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

1. **Wait and Timeout Patterns**:

   - **Never use `asyncio.sleep()` for page load waits** - use `wait_for_load_state()` instead
   - Use `asyncio.timeout()` context manager for operation-level timeout control
   - Navigation tools pattern:
     ```python
     try:
         await _wait_for_page_ready("load", timeout_ms=timeout)
     except TimeoutError:
         # Log warning but continue to get partial page info
         logger.warning("Page load timeout, attempting to get current state")
     ```
   - `asyncio.sleep()` is acceptable only for polling intervals in wait loops (e.g., 100ms polling)
   - Use appropriate load states: `"load"` for full page, `"domcontentloaded"` for history navigation
   - History navigation typically uses shorter timeout (5s) vs full navigation (30s+)

### Development Workflow

This project uses `uv` for dependency management and task automation. All development tasks should be run through `make` commands or `uv run`.

**Available Make Commands:**

```bash
# Setup and Installation
make install          # Create virtual environment and install pre-commit hooks

# Code Quality
make check            # Run all code quality checks (lock file, linting, dependency check)
                     # This runs: uv lock --locked, pre-commit, and deptry

# Testing
make test            # Run pytest with coverage reporting
                     # Use: uv run python -m pytest (not direct pytest)

# Building
make build           # Build wheel file for distribution
make clean-build     # Clean build artifacts
```

**Running Commands Manually:**

Always use `uv run` prefix when running Python tools:

```bash
# Correct - using uv run
uv run pytest tests/
uv run python -m pytest tests/ --cov=pai_browser_use
uv run pre-commit run -a
uv run deptry .

# Incorrect - direct invocation
pytest tests/          # ❌ Don't do this
python -m pytest       # ❌ Don't do this
```

**Pre-commit Workflow:**

The project uses pre-commit hooks for code quality:

- Runs automatically on `git commit`
- Can be run manually with `make check` or `uv run pre-commit run -a`
- Includes: ruff (linting), ruff format, file checks, JSON/YAML/TOML validation

## Dependencies

- `cdp-use`: CDP client library
- `pydantic-ai`: Agent framework with toolset support
- `pillow`: Image processing for screenshot splitting
- `httpx`: HTTP client for CDP endpoint discovery

## Testing

### Test Architecture

The test suite uses a Docker-based architecture with two containers:

1. **Nginx Container** (`test-server`): Serves local HTML test files from `tests/test_fixtures/`
1. **Chrome Container** (`chrome-test`): Headless Chrome browser for CDP testing
1. **Docker Network** (`pai-test-network`): Allows containers to communicate

**Key Benefits:**

- No external dependencies (example.com no longer used)
- Fully offline testing capability
- Predictable and controllable test pages
- Faster test execution (no network latency)
- Better CI/CD reliability

### Test Fixtures

Test HTML files are organized in `tests/test_fixtures/`:

- `basic.html` - Basic page elements (h1, p, div, links)
- `forms.html` - Form controls (input, select, checkbox, radio, file upload)
- `interactive.html` - Interactive elements (buttons, hover, scroll)
- `navigation/page*.html` - Multi-page navigation testing
- `dialogs.html` - JavaScript dialog triggers (alert, confirm, prompt)
- `dynamic.html` - Dynamic content and delayed elements
- `long_page.html` - Long page for screenshot segmentation testing

### Running Tests

**IMPORTANT:** Always use `uv run` or `make test` to run tests:

```bash
# Run all tests (recommended)
make test

# Run all tests manually
uv run python -m pytest tests/

# Run specific test file
uv run pytest tests/test_navigation.py -v

# Run with coverage
uv run pytest tests/ --cov=pai_browser_use

# Skip slow Docker-based tests (run only unit tests)
uv run pytest tests/test_image_utils.py tests/test_tools.py -v

# Verbose output
uv run pytest tests/ -vv
```

### Test Fixture Usage

Tests receive the `test_server` fixture which provides the base URL:

```python
async def test_example(cdp_url, test_server):
    async with BrowserUseToolset(cdp_url) as toolset:
        session = toolset._browser_session
        nav_tool = build_tool(session, navigate_to_url)
        await nav_tool.function_schema.call(
            {"url": f"{test_server}/test_fixtures/basic.html"},
            None
        )
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

# Basic navigation and screenshot
result = await agent.run("Navigate to example.com and take a screenshot")

# Form interaction example
result = await agent.run("""
    Go to the search page, wait for the search input to appear,
    type 'browser automation', select 'All results' from the filter dropdown,
    check the 'Include archived' checkbox, and submit the form
""")

# Advanced interaction example
result = await agent.run("""
    Navigate to the menu page, hover over 'Products' to show the dropdown,
    wait for the submenu to appear, then click on 'Documentation'
""")
```
