"""Tests for the CLI module."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from codegate.cli import cli
from codegate.codegate_logging import LogFormat, LogLevel
from codegate.config import DEFAULT_PROVIDER_URLS


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_logging(monkeypatch: Any) -> MagicMock:
    """Mock the logging function."""
    mock = MagicMock()
    monkeypatch.setattr("codegate.cli.structlog.get_logger", mock)
    return mock


@pytest.fixture
def mock_setup_logging(monkeypatch: Any) -> MagicMock:
    """Mock the setup_logging function."""
    mock = MagicMock()
    monkeypatch.setattr("codegate.cli.setup_logging", mock)
    return mock


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
port: 8989
host: localhost
log_level: DEBUG
log_format: JSON
"""
    )
    return config_file


def test_cli_version(cli_runner: CliRunner) -> None:
    """Test CLI version command."""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_serve_default_options(
    cli_runner: CliRunner, mock_logging: Any, mock_setup_logging: Any
) -> None:
    """Test serve command with default options."""
    with patch("uvicorn.run") as mock_run:
        logger_instance = MagicMock()
        mock_logging.return_value = logger_instance
        result = cli_runner.invoke(cli, ["serve"])

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(LogLevel.INFO, LogFormat.JSON)
        mock_logging.assert_called_with("codegate")
        logger_instance.info.assert_any_call(
            "Starting server",
            extra={
                "host": "localhost",
                "port": 8989,
                "log_level": "INFO",
                "log_format": "JSON",
                "prompts_loaded": 7,  # Default prompts are loaded
                "provider_urls": DEFAULT_PROVIDER_URLS,
            },
        )
        mock_run.assert_called_once()


def test_serve_custom_options(
    cli_runner: CliRunner, mock_logging: Any, mock_setup_logging: Any
) -> None:
    """Test serve command with custom options."""
    with patch("uvicorn.run") as mock_run:
        logger_instance = MagicMock()
        mock_logging.return_value = logger_instance
        result = cli_runner.invoke(
            cli,
            [
                "serve",
                "--port",
                "8989",
                "--host",
                "localhost",
                "--log-level",
                "DEBUG",
                "--log-format",
                "TEXT",
            ],
        )

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(LogLevel.DEBUG, LogFormat.TEXT)
        mock_logging.assert_called_with("codegate")
        logger_instance.info.assert_any_call(
            "Starting server",
            extra={
                "host": "localhost",
                "port": 8989,
                "log_level": "DEBUG",
                "log_format": "TEXT",
                "prompts_loaded": 7,  # Default prompts are loaded
                "provider_urls": DEFAULT_PROVIDER_URLS,
            },
        )
        mock_run.assert_called_once()


def test_serve_invalid_port(cli_runner: CliRunner) -> None:
    """Test serve command with invalid port."""
    result = cli_runner.invoke(cli, ["serve", "--port", "999999"])
    assert result.exit_code == 2
    assert "Port must be between 1 and 65535" in result.output


def test_serve_invalid_log_level(cli_runner: CliRunner) -> None:
    """Test serve command with invalid log level."""
    result = cli_runner.invoke(cli, ["serve", "--log-level", "INVALID"])
    assert result.exit_code == 2
    assert "Invalid value for '--log-level'" in result.output


def test_serve_with_config_file(
    cli_runner: CliRunner, mock_logging: Any, temp_config_file: Path, mock_setup_logging: Any
) -> None:
    """Test serve command with config file."""
    with patch("uvicorn.run") as mock_run:
        logger_instance = MagicMock()
        mock_logging.return_value = logger_instance
        result = cli_runner.invoke(cli, ["serve", "--config", str(temp_config_file)])

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(LogLevel.DEBUG, LogFormat.JSON)
        mock_logging.assert_called_with("codegate")
        logger_instance.info.assert_any_call(
            "Starting server",
            extra={
                "host": "localhost",
                "port": 8989,
                "log_level": "DEBUG",
                "log_format": "JSON",
                "prompts_loaded": 7,  # Default prompts are loaded
                "provider_urls": DEFAULT_PROVIDER_URLS,
            },
        )
        mock_run.assert_called_once()


def test_serve_with_nonexistent_config_file(cli_runner: CliRunner) -> None:
    """Test serve command with nonexistent config file."""
    result = cli_runner.invoke(cli, ["serve", "--config", "nonexistent.yaml"])
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_serve_priority_resolution(
    cli_runner: CliRunner,
    mock_logging: Any,
    temp_config_file: Path,
    env_vars: Any,
    mock_setup_logging: Any,
) -> None:
    """Test serve command respects configuration priority."""
    with patch("uvicorn.run") as mock_run:
        logger_instance = MagicMock()
        mock_logging.return_value = logger_instance
        result = cli_runner.invoke(
            cli,
            [
                "serve",
                "--config",
                str(temp_config_file),
                "--port",
                "8080",
                "--host",
                "example.com",
                "--log-level",
                "ERROR",
                "--log-format",
                "TEXT",
            ],
        )

        assert result.exit_code == 0
        mock_setup_logging.assert_called_once_with(LogLevel.ERROR, LogFormat.TEXT)
        mock_logging.assert_called_with("codegate")
        logger_instance.info.assert_any_call(
            "Starting server",
            extra={
                "host": "example.com",
                "port": 8080,
                "log_level": "ERROR",
                "log_format": "TEXT",
                "prompts_loaded": 7,  # Default prompts are loaded
                "provider_urls": DEFAULT_PROVIDER_URLS,
            },
        )
        mock_run.assert_called_once()


def test_main_function() -> None:
    """Test main function."""
    with patch("codegate.cli.cli") as mock_cli:
        from codegate.cli import main

        main()
        mock_cli.assert_called_once()
