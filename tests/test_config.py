"""Tests for configuration management using pydantic-settings."""

from pai_browser_use._config import BrowserUseSettings
from pai_browser_use.toolset import BrowserUseToolset


def test_browser_use_settings_defaults():
    """Test that BrowserUseSettings has correct default values."""
    settings = BrowserUseSettings()
    assert settings.max_retries is None
    assert settings.prefix is None
    assert settings.always_use_new_page is None


def test_browser_use_settings_from_env(monkeypatch):
    """Test that BrowserUseSettings loads from environment variables."""
    # Set environment variables
    monkeypatch.setenv("PAI_BROWSER_USE_MAX_RETRIES", "5")
    monkeypatch.setenv("PAI_BROWSER_USE_PREFIX", "custom_prefix")
    monkeypatch.setenv("PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE", "true")

    settings = BrowserUseSettings()
    assert settings.max_retries == 5
    assert settings.prefix == "custom_prefix"
    assert settings.always_use_new_page is True


def test_browser_use_toolset_uses_settings_defaults():
    """Test that BrowserUseToolset uses fallback defaults when settings and parameters are None."""
    toolset = BrowserUseToolset(cdp_url="http://localhost:9222/json/version")
    assert toolset.max_retries == 3  # Default fallback
    assert toolset.prefix == "browser_use"  # Default to toolset.id
    assert toolset.always_use_new_page is False  # Default fallback


def test_browser_use_toolset_uses_env_settings(monkeypatch):
    """Test that BrowserUseToolset uses environment variables when parameters are None."""
    # Set environment variables
    monkeypatch.setenv("PAI_BROWSER_USE_MAX_RETRIES", "10")
    monkeypatch.setenv("PAI_BROWSER_USE_PREFIX", "env_browser")
    monkeypatch.setenv("PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE", "true")

    toolset = BrowserUseToolset(cdp_url="http://localhost:9222/json/version")
    assert toolset.max_retries == 10
    assert toolset.prefix == "env_browser"
    assert toolset.always_use_new_page is True


def test_browser_use_toolset_parameters_override_env(monkeypatch):
    """Test that explicit parameters override environment variables."""
    # Set environment variables
    monkeypatch.setenv("PAI_BROWSER_USE_MAX_RETRIES", "10")
    monkeypatch.setenv("PAI_BROWSER_USE_PREFIX", "env_browser")
    monkeypatch.setenv("PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE", "true")

    # Create toolset with explicit parameters
    toolset = BrowserUseToolset(
        cdp_url="http://localhost:9222/json/version",
        max_retries=20,
        prefix="param_browser",
        always_use_new_page=False,
    )

    # Parameters should override environment variables
    assert toolset.max_retries == 20
    assert toolset.prefix == "param_browser"
    assert toolset.always_use_new_page is False


def test_browser_use_toolset_partial_parameter_override(monkeypatch):
    """Test that only provided parameters override environment variables."""
    # Set environment variables
    monkeypatch.setenv("PAI_BROWSER_USE_MAX_RETRIES", "10")
    monkeypatch.setenv("PAI_BROWSER_USE_PREFIX", "env_browser")
    monkeypatch.setenv("PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE", "true")

    # Create toolset with only max_retries parameter
    toolset = BrowserUseToolset(
        cdp_url="http://localhost:9222/json/version",
        max_retries=20,  # Override env
        # prefix and always_use_new_page will use env values
    )

    assert toolset.max_retries == 20  # Overridden by parameter
    assert toolset.prefix == "env_browser"  # From environment
    assert toolset.always_use_new_page is True  # From environment


def test_browser_use_settings_env_file_loading(tmp_path, monkeypatch):
    """Test that BrowserUseSettings can load from .env file."""
    # Create a temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PAI_BROWSER_USE_MAX_RETRIES=15\n"
        "PAI_BROWSER_USE_PREFIX=file_browser\n"
        "PAI_BROWSER_USE_ALWAYS_USE_NEW_PAGE=false\n"
    )

    # Change to temp directory to pick up .env file
    monkeypatch.chdir(tmp_path)

    settings = BrowserUseSettings()
    assert settings.max_retries == 15
    assert settings.prefix == "file_browser"
    assert settings.always_use_new_page is False
