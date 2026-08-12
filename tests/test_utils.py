"""Tests for log_analyzer_cli.utils."""

from log_analyzer_cli.utils import _try_parse_datetime


def test_apache_timestamp_with_positive_offset():
    # Apache combined log format always includes a timezone offset.
    # Before the fix, _try_parse_datetime returned None for this input
    # because the format list had only "%d/%b/%Y:%H:%M:%S" (no %z).
    result = _try_parse_datetime("01/Jan/2025:12:00:00 +0000")
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12
    assert result.utcoffset().total_seconds() == 0


def test_apache_timestamp_with_negative_offset():
    # Real-world Apache access lines commonly use a negative offset.
    # 10/Oct/2000:13:55:36 -0700 is the canonical example from the Apache docs.
    result = _try_parse_datetime("10/Oct/2000:13:55:36 -0700")
    assert result is not None
    assert result.year == 2000
    assert result.hour == 13
    assert result.utcoffset().total_seconds() == -7 * 3600


def test_apache_timestamp_without_offset_still_works():
    # The naive form (no offset) must still parse for back-compat with
    # logs that predate the offset inclusion.
    result = _try_parse_datetime("01/Jan/2025:12:00:00")
    assert result is not None
    assert result.hour == 12
