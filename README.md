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
