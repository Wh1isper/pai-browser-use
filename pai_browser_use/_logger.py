import os

USER_DEFINED_LOG_LEVEL = os.getenv("PAI_BROWSER_USE_LOG_LEVEL", "ERROR")

os.environ["LOGURU_LEVEL"] = USER_DEFINED_LOG_LEVEL

from loguru import logger  # noqa: E402

__all__ = ["logger"]
