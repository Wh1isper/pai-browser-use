"""This is an example of using BrowserUseToolset in a Pydantic AI agent

Before running this example, make sure you have a running CDP endpoint.
You can use Chrome or Chromium with the --remote-debugging-port flag:
    google-chrome --remote-debugging-port=9222
Or you can run `dev/start-browser-container.sh` to start a Chrome container with CDP enabled.
"""

from dotenv import load_dotenv

load_dotenv()

import os

from pydantic_ai import Agent

from pai_browser_use import BrowserUseToolset

MODEL_NAME = os.getenv("MODEL_NAME", "anthropic:claude-sonnet-4-5")


async def main():
    agent = Agent(
        model=MODEL_NAME,
        system_prompt="You are a helpful assistant.",
        toolsets=[
            BrowserUseToolset(cdp_url="http://localhost:9222/json/version"),  # or a direct ws:// URL
        ],
    )
    result = await agent.run("Find the number of stars of the wh1isper/pai-browser-use repo")
    print(result.output)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
