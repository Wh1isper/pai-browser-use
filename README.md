# pai-browser-use

[![Release](https://img.shields.io/github/v/release/wh1isper/pai-browser-use)](https://img.shields.io/github/v/release/wh1isper/pai-browser-use)
[![Build status](https://img.shields.io/github/actions/workflow/status/wh1isper/pai-browser-use/main.yml?branch=main)](https://github.com/wh1isper/pai-browser-use/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/wh1isper/pai-browser-use/branch/main/graph/badge.svg)](https://codecov.io/gh/wh1isper/pai-browser-use)
[![Commit activity](https://img.shields.io/github/commit-activity/m/wh1isper/pai-browser-use)](https://img.shields.io/github/commit-activity/m/wh1isper/pai-browser-use)
[![License](https://img.shields.io/github/license/wh1isper/pai-browser-use)](https://img.shields.io/github/license/wh1isper/pai-browser-use)

Pydantic AI Toolsets for browser automation using Chrome DevTools Protocol (CDP).

Inspired by [browser-use](https://github.com/browser-use/browser-use), designed for [Pydantic AI](https://ai.pydantic.dev/) agents.

## Features

- **Browser Automation Tools**: Navigation, state inspection, interaction, and element queries
- **Multi-Modal Screenshots**: Automatic image splitting for long pages with ToolReturn support
- **Type-Safe CDP Integration**: Direct access to cdp-use API with full type hints
- **Fully Tested**: Comprehensive test suite with Docker-based Chrome container

## Installation

Use pip:

```bash
pip install pai-browser-use
```

Or use uv:

```bash
uv add pai-browser-use
```

## Quick Start

### Prerequisites

Start a Chrome instance with CDP enabled:

```bash
# Option 1: Using Chrome directly
google-chrome --remote-debugging-port=9222

# Option 2: Using Docker container
./dev/start-browser-container.sh
```

### Basic Usage

```python
import os
from pydantic_ai import Agent
from pai_browser_use import BrowserUseToolset

agent = Agent(
    model="anthropic:claude-sonnet-4-5",
    system_prompt="You are a helpful assistant.",
    toolsets=[
        BrowserUseToolset(cdp_url="http://localhost:9222/json/version"),
    ],
)

result = await agent.run("Find the number of stars of the wh1isper/pai-browser-use repo")
print(result.output)
```

See [examples/agent.py](examples/agent.py) for a complete example.

## Available Tools

**Navigation** (4 tools)

- `navigate_to_url`, `go_back`, `go_forward`, `reload_page`

**State Inspection** (5 tools)

- `get_page_info`, `get_page_content`, `take_screenshot`, `take_element_screenshot`, `get_viewport_info`

**Interaction** (4 tools)

- `click_element`, `type_text`, `execute_javascript`, `scroll_to`

**Query** (3 tools)

- `find_elements`, `get_element_text`, `get_element_attributes`

## Logging

The project includes detailed INFO level logging for debugging and development. By default, only ERROR logs are shown.

### Enable Detailed Logging

```bash
# Set log level via environment variable
export PAI_BROWSER_USE_LOG_LEVEL=INFO

# Then run your script
python your_script.py
```

### Available Log Levels

- `ERROR` (default): Only show errors
- `WARNING`: Show warnings and errors
- `INFO`: Show detailed operation flow
- `DEBUG`: Show all debugging information including actual data

### What Gets Logged

**INFO level** shows:

- CDP connection establishment
- Browser target creation/reuse
- Tool execution lifecycle
- Page navigation steps
- Screenshot capture and processing
- Element interactions and queries
- Session state updates
- Resource cleanup

**DEBUG level** additionally shows:

- **Extracted text content** (first 500 characters)
- **HTML content preview** (first 500 characters)
- **Element details** (tag, text, attributes, position)
- **JavaScript execution results**
- **Tool call arguments and return types**
- **Full page information** (URL, title, viewport)
- All intermediate data for debugging

### Examples

**INFO Level** - See operation flow:

```python
import os
os.environ["PAI_BROWSER_USE_LOG_LEVEL"] = "INFO"

from pai_browser_use import BrowserUseToolset

async with BrowserUseToolset(cdp_url="http://localhost:9222/json/version") as toolset:
    # Shows what operations are being performed
    pass
```

**DEBUG Level** - See actual data:

```python
import os
os.environ["PAI_BROWSER_USE_LOG_LEVEL"] = "DEBUG"

from pai_browser_use.tools.state import get_page_content

# Will show the actual text/HTML extracted
content = await get_page_content(content_format="text")
# DEBUG log shows: "Text content preview (first 500 chars): ..."
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
pytest tests/

# Run example
python examples/agent.py

# Try DEBUG logging demo (shows extracted content)
PAI_BROWSER_USE_LOG_LEVEL=DEBUG python demo_debug_logging.py
```

## License

BSD 3-Clause License - see [LICENSE](LICENSE) for details.
