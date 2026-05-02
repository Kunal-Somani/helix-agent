"""Unit tests for configuration module."""

import pytest
from app.config import settings


def test_settings_loaded():
    """Test that settings load successfully."""
    assert settings is not None
    assert settings.ENVIRONMENT in ["development", "production"]
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_required_settings_exist():
    """Test that required settings are present."""
    # These should raise an error if not set in .env
    # For CI/CD, they should be mocked
    assert hasattr(settings, "ANTHROPIC_API_KEY")
    assert hasattr(settings, "MY_EMAIL")
    assert hasattr(settings, "MY_SECRET")


def test_default_settings():
    """Test default setting values."""
    assert settings.REDIS_URL == "redis://localhost:6379"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.ENVIRONMENT == "development"
