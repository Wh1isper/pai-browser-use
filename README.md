# pai-browser-use

[![Release](https://img.shields.io/github/v/release/wh1isper/pai-browser-use)](https://img.shields.io/github/v/release/wh1isper/pai-browser-use)
[![Build status](https://img.shields.io/github/actions/workflow/status/wh1isper/pai-browser-use/main.yml?branch=main)](https://github.com/wh1isper/pai-browser-use/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/wh1isper/pai-browser-use/branch/main/graph/badge.svg)](https://codecov.io/gh/wh1isper/pai-browser-use)
[![Commit activity](https://img.shields.io/github/commit-activity/m/wh1isper/pai-browser-use)](https://img.shields.io/github/commit-activity/m/wh1isper/pai-browser-use)
[![License](https://img.shields.io/github/license/wh1isper/pai-browser-use)](https://img.shields.io/github/license/wh1isper/pai-browser-use)

> **⚠️ Early Stage Project**
> This project is currently in early development. APIs and features may change. We welcome your feedback and contributions!
>
> - 🐛 Found a bug? [Submit an issue](https://github.com/wh1isper/pai-browser-use/issues/new)
> - 💡 Have ideas or suggestions? [Join the discussion](https://github.com/wh1isper/pai-browser-use/discussions)
> - 🤝 Want to contribute? Check out our [Contributing Guide](CONTRIBUTING.md)

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
import asyncio
from pydantic_ai import Agent
from pai_browser_use import BrowserUseToolset

async def main():
    agent = Agent(
        model="openai:gpt-5",
        system_prompt="You are a helpful assistant.",
        toolsets=[
            BrowserUseToolset(cdp_url="http://localhost:9222/json/version"),
        ],
    )

    result = await agent.run("Find the number of stars of the wh1isper/pai-browser-use repo")
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

See [examples/agent.py](examples/agent.py) for a complete example.

## Configuration

BrowserUseToolset supports configuration via environment variables. See [.env.example](.env.example) for all available options.

You can override environment variables by passing explicit parameters:

```python
toolset = BrowserUseToolset(
    cdp_url="http://localhost:9222/json/version",
    max_retries=10,              # Override PAI_BROWSER_USE_MAX_RETRIES
    prefix="custom_browser",     # Override PAI_BROWSER_USE_PREFIX
    always_use_new_page=True,    # Override PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE
    auto_cleanup_page=False,     # Override PAI_BROWSER_USE_AUTO_CLEANUP_PAGE
)
```

**Priority**: Explicit parameters > Environment variables > Defaults

### Page Management

- **`always_use_new_page`**: When `True`, creates a new browser page instead of reusing existing ones. Defaults to `False`.
- **`auto_cleanup_page`**: When `True`, automatically closes created pages on context exit. Defaults to `False`.

**Use Case Examples:**

```python
# Default behavior: Reuse existing page, no cleanup needed
toolset = BrowserUseToolset(cdp_url="http://localhost:9222/json/version")

# Create new page but keep it open for debugging/inspection (default when using always_use_new_page)
toolset = BrowserUseToolset(
    cdp_url="http://localhost:9222/json/version",
    always_use_new_page=True,   # Create fresh page
    # auto_cleanup_page defaults to False - page remains open
)

# Create new page and automatically clean up (for production/batch processing)
toolset = BrowserUseToolset(
    cdp_url="http://localhost:9222/json/version",
    always_use_new_page=True,   # Create fresh page
    auto_cleanup_page=True,     # Clean up after execution
)
```

## Logging

Use `PAI_BROWSER_USE_LOG_LEVEL` environment variable to set logging level. The default is `ERROR`. Set to `DEBUG` for more verbose logging.

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
