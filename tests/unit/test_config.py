"""Tests for configuration."""

import os
from unittest.mock import patch

from resume_screener.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_with_defaults(self) -> None:
        """Test settings with default values."""
        settings = Settings(openai_api_key="test-key")
        assert settings.openai_api_key == "test-key"
        assert settings.openai_model == "gpt-4"
        assert settings.log_level == "INFO"
        assert settings.jd_file_path == "resources/job_description.pdf"

    def test_settings_custom_values(self) -> None:
        """Test settings with custom values."""
        settings = Settings(
            openai_api_key="custom-key",
            openai_model="gpt-3.5-turbo",
            log_level="DEBUG",
            jd_file_path="/custom/path/jd.pdf",
        )
        assert settings.openai_api_key == "custom-key"
        assert settings.openai_model == "gpt-3.5-turbo"
        assert settings.log_level == "DEBUG"
        assert settings.jd_file_path == "/custom/path/jd.pdf"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings(self) -> None:
        """Test get_settings returns Settings instance."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-test-key"}):
            get_settings.cache_clear()
            settings = get_settings()
            assert isinstance(settings, Settings)
            assert settings.openai_api_key == "env-test-key"

    def test_get_settings_cached(self) -> None:
        """Test get_settings returns cached instance."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "cached-key"}):
            get_settings.cache_clear()
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2
