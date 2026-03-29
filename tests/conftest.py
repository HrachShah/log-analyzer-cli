"""Test configuration for pytest."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def examples_dir() -> Path:
    """Return path to examples directory."""
    return Path(__file__).parent.parent / "examples"


@pytest.fixture
def syslog_file(examples_dir) -> Path:
    """Return path to syslog sample file."""
    return examples_dir / "syslog-sample.log"


@pytest.fixture
def apache_file(examples_dir) -> Path:
    """Return path to apache sample file."""
    return examples_dir / "apache-sample.log"


@pytest.fixture
def json_file(examples_dir) -> Path:
    """Return path to JSON sample file."""
    return examples_dir / "app-json.log"


@pytest.fixture
def mixed_file(examples_dir) -> Path:
    """Return path to mixed sample file."""
    return examples_dir / "mixed.log"


@pytest.fixture
def sample_lines():
    """Return sample log lines for testing."""
    return {
        "syslog": "2025-03-20 10:15:32 systemkernel: System boot completed",
        "apache": '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0"',
        "json": '{"timestamp": "2025-03-20T10:15:32.123Z", "level": "INFO", "message": "Application started"}',
        "generic": "2025-03-20T10:15:32.123Z INFO Application started successfully",
    }
