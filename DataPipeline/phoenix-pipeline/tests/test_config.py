"""Tests for configuration module."""

import pytest
from pathlib import Path

from phoenix_pipeline.config import Settings


class TestSettings:
    """Test suite for Settings."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()

        assert settings.batch_size == 100
        assert settings.start_block == 0
        assert settings.output_format == "csv"
        assert settings.log_level == "INFO"

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading settings from environment variables."""
        monkeypatch.setenv("BATCH_SIZE", "200")
        monkeypatch.setenv("START_BLOCK", "1000")
        monkeypatch.setenv("OUTPUT_FORMAT", "json")

        settings = Settings()

        assert settings.batch_size == 200
        assert settings.start_block == 1000
        assert settings.output_format == "json"

    def test_output_dir_creation(self, tmp_path: Path) -> None:
        """Test that output directory is created."""
        output_dir = tmp_path / "test_output"
        settings = Settings(output_dir=output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_invalid_output_format(self) -> None:
        """Test validation of output format."""
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(output_format="invalid")

    def test_invalid_log_level(self) -> None:
        """Test validation of log level."""
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(log_level="INVALID")

    def test_batch_size_validation(self) -> None:
        """Test batch size must be >= 1."""
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(batch_size=0)
