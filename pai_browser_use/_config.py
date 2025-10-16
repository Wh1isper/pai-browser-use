"""Configuration management using pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BrowserUseSettings(BaseSettings):
    """Configuration for BrowserUseToolset with environment variable support.

    All settings can be overridden via environment variables with the prefix PAI_BROWSER_USE_.
    For example, to set max_retries, use PAI_BROWSER_USE_MAX_RETRIES=5.
    """

    model_config = SettingsConfigDict(
        env_prefix="PAI_BROWSER_USE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_retries: int | None = None
    """Maximum retry attempts for tool calls. Defaults to None (no retry limit set by config)."""

    prefix: str | None = None
    """Tool name prefix. Defaults to None (will use toolset ID)."""

    always_use_new_page: bool | None = None
    """Force create new page instead of reusing existing. Defaults to None (will use False)."""
