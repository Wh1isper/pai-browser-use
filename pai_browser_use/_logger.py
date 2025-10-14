import os
import sys

from loguru import logger as _logger

USER_DEFINED_LOG_LEVEL = os.getenv("PAI_BROWSER_USE_LOG_LEVEL", "ERROR")

logger = _logger.bind(module="pai_browser_use")
logger.remove()
logger.add(
    sys.stderr,
    level=USER_DEFINED_LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    filter=lambda record: record["extra"].get("module") == "pai_browser_use",
)

__all__ = ["logger"]
