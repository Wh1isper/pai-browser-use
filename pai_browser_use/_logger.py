import logging
import os
import sys
from typing import ClassVar


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "GREEN": "\033[32m",  # Green for timestamp
        "CYAN": "\033[36m",  # Cyan for location
    }

    def format(self, record: logging.LogRecord) -> str:
        # Format timestamp
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        colored_timestamp = f"{self.COLORS['GREEN']}{timestamp}{self.COLORS['RESET']}"

        # Format level with padding
        level = record.levelname
        colored_level = f"{self.COLORS.get(level, '')}{level:<8}{self.COLORS['RESET']}"

        # Format location (name:function:line)
        location = f"{self.COLORS['CYAN']}{record.name}:{record.funcName}:{record.lineno}{self.COLORS['RESET']}"

        # Format message with level color
        colored_message = f"{self.COLORS.get(level, '')}{record.getMessage()}{self.COLORS['RESET']}"

        return f"{colored_timestamp} | {colored_level} | {location} - {colored_message}"


def _setup_logger() -> logging.Logger:
    """Setup and configure the logger for pai_browser_use."""
    log_level_name = os.getenv("PAI_BROWSER_USE_LOG_LEVEL", "ERROR").upper()
    log_level = getattr(logging, log_level_name, logging.ERROR)

    # Create logger
    _logger = logging.getLogger("pai_browser_use")
    _logger.setLevel(log_level)
    _logger.propagate = False

    # Remove existing handlers
    _logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)

    # Set formatter (use colored if terminal supports it)
    if sys.stderr.isatty():
        formatter = ColoredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    return _logger


logger = _setup_logger()

__all__ = ["logger"]
