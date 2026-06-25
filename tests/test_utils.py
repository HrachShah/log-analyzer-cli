"""Tests for log_analyzer_cli.utils."""

from __future__ import annotations

import pytest

from log_analyzer_cli.utils import detect_log_level


pytestmark = pytest.mark.unit


def test_detect_log_level_simple_keyword():
    """A bare level keyword returns that level."""
    assert detect_log_level("ERROR something failed") == "ERROR"
    assert detect_log_level("WARN disk almost full") == "WARNING"
    assert detect_log_level("[INFO] started") == "INFO"
    assert detect_log_level("[DEBUG] enter") == "DEBUG"
    assert detect_log_level("[TRACE] loop") == "TRACE"
    assert detect_log_level("[CRIT] panic") == "CRITICAL"
    assert detect_log_level("[ERR] oops") == "ERROR"


def test_detect_log_level_timestamped():
    """A leading timestamp before the level still detects the level."""
    assert detect_log_level("2024-01-15 10:23:45 ERROR Connection failed") == "ERROR"
    assert detect_log_level("2024-01-15T10:23:45 INFO starting up") == "INFO"


def test_detect_log_level_picks_earliest_match():
    """When a line contains multiple level keywords, the leftmost wins.

    Before the fix, detect_log_level iterated the level-pattern list in a
    hard-coded order and returned the first level whose regex matched
    *anywhere* in the line. So a line like
    "2024-01-15 10:23:45 WARNING cannot connect to CRITICAL service"
    was misclassified as CRITICAL even though the actual log entry is a
    WARNING, because CRITICAL comes first in the pattern list.
    """
    line = "2024-01-15 10:23:45 WARNING cannot connect to CRITICAL service"
    assert detect_log_level(line) == "WARNING"


def test_detect_log_level_earlier_critical_wins():
    """The leftmost match still wins when it is the higher-severity level."""
    line = "2024-01-15 10:23:45 CRITICAL followed by INFO context"
    assert detect_log_level(line) == "CRITICAL"


def test_detect_log_level_returns_unknown_for_non_level_lines():
    """Lines without any level keyword return UNKNOWN."""
    assert detect_log_level("just a regular message") == "UNKNOWN"
    assert detect_log_level("") == "UNKNOWN"
    assert detect_log_level("   ") == "UNKNOWN"


def test_detect_log_level_ignores_substring_matches():
    """Levels embedded inside other identifiers do not match.

    The regex uses \\b word boundaries, so ERROR_RATE / WARNING_THRESHOLD
    do not count as level hits. This is the same as before the fix; the
    regression test here is to make sure the reordering of the pattern
    list does not accidentally drop the word boundaries.
    """
    assert detect_log_level("ERROR_RATE exceeded threshold") == "UNKNOWN"
    assert detect_log_level("retried after WARNING_THRESHOLD") == "UNKNOWN"
    assert detect_log_level("CRITICAL_ERROR was set") == "UNKNOWN"


def test_detect_log_level_case_insensitive():
    """The detection is case-insensitive."""
    assert detect_log_level("error something") == "ERROR"
    assert detect_log_level("warning something") == "WARNING"
    assert detect_log_level("Info something") == "INFO"
