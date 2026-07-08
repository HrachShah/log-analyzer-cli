"""Tests for log_analyzer_cli.utils."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from log_analyzer_cli.utils import (
    detect_log_level,
    filter_lines,
    normalize_error_pattern,
    parse_timestamp,
    read_log_file,
)


class TestParseTimestamp:
    """Tests for parse_timestamp."""

    def test_iso_microseconds_with_offset(self) -> None:
        """ISO 8601 with microseconds AND a numeric offset is a common
        Python `datetime.isoformat()` output and must not be dropped.
        """
        result = parse_timestamp("2025-10-10T13:55:36.123456+00:00 INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, 123456, tzinfo=timezone.utc)

    def test_iso_microseconds_with_z(self) -> None:
        """ISO 8601 with microseconds and a trailing Z must round-trip."""
        result = parse_timestamp("2025-10-10T13:55:36.123456Z INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, 123456, tzinfo=timezone.utc)

    def test_iso_microseconds_with_negative_offset(self) -> None:
        result = parse_timestamp("2025-10-10T13:55:36.123456-0700 INFO hello world")
        expected_tz = timezone(timedelta(hours=-7))
        assert result == datetime(2025, 10, 10, 13, 55, 36, 123456, tzinfo=expected_tz)

    def test_iso_space_separator_with_microseconds_and_offset(self) -> None:
        result = parse_timestamp("2025-10-10 13:55:36.123456+00:00 INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, 123456, tzinfo=timezone.utc)

    def test_iso_without_fractional_with_offset(self) -> None:
        result = parse_timestamp("2025-10-10T13:55:36+00:00 INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, tzinfo=timezone.utc)

    def test_iso_without_fractional_with_z(self) -> None:
        result = parse_timestamp("2025-10-10T13:55:36Z INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, tzinfo=timezone.utc)

    def test_iso_with_fractional_no_tz(self) -> None:
        result = parse_timestamp("2025-10-10T13:55:36.123456 INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36, 123456)

    def test_iso_space_separator_no_fractional(self) -> None:
        result = parse_timestamp("2025-10-10 13:55:36 INFO hello world")
        assert result == datetime(2025, 10, 10, 13, 55, 36)

    def test_apache_common_log_with_offset(self) -> None:
        """Apache common log format with numeric offset."""
        result = parse_timestamp("10/Oct/2025:13:55:36 -0700 GET /")
        expected_tz = timezone(timedelta(hours=-7))
        assert result == datetime(2025, 10, 10, 13, 55, 36, tzinfo=expected_tz)

    def test_apache_common_log_no_tz(self) -> None:
        result = parse_timestamp("10/Oct/2025:13:55:36 GET /")
        assert result == datetime(2025, 10, 10, 13, 55, 36)

    def test_syslog_rfc3164_no_year(self) -> None:
        result = parse_timestamp("Mar 20 10:15:32 hostname process: foo")
        assert result is not None
        assert result.month == 3
        assert result.day == 20
        assert result.hour == 10
        assert result.minute == 15
        assert result.second == 32

    def test_no_timestamp_returns_none(self) -> None:
        assert parse_timestamp("just a plain line with no timestamp") is None

    def test_fractional_seconds_are_preserved(self) -> None:
        """Microseconds from the input must survive parsing — earlier formats
        that didn't include %f would silently truncate to 0.
        """
        result = parse_timestamp("2025-10-10T13:55:36.123456+00:00")
        assert result is not None
        assert result.microsecond == 123456

    def test_offset_is_preserved(self) -> None:
        """A timestamp with a numeric offset must keep that offset — earlier
        formats that didn't include %z would silently return a naive datetime.
        """
        result = parse_timestamp("2025-10-10T13:55:36.123456-0700")
        assert result is not None
        assert result.utcoffset() == timedelta(hours=-7)
        # And a +00:00 offset must be reported as UTC-aware, not naive.
        utc_result = parse_timestamp("2025-10-10T13:55:36+00:00")
        assert utc_result is not None
        assert utc_result.tzinfo is not None


class TestDetectLogLevel:
    def test_error(self) -> None:
        assert detect_log_level("2025-10-10 ERROR something failed") == "ERROR"

    def test_warning(self) -> None:
        assert detect_log_level("2025-10-10 WARN deprecated") == "WARNING"

    def test_info(self) -> None:
        assert detect_log_level("2025-10-10 INFO started") == "INFO"

    def test_debug(self) -> None:
        assert detect_log_level("2025-10-10 DEBUG trace") == "DEBUG"

    def test_critical(self) -> None:
        assert detect_log_level("2025-10-10 CRITICAL out of memory") == "CRITICAL"

    def test_unknown(self) -> None:
        assert detect_log_level("2025-10-10 hello world") == "UNKNOWN"


class TestNormalizeErrorPattern:
    def test_ips_replaced(self) -> None:
        assert normalize_error_pattern("connection to 192.168.1.1 failed") == \
            "connection to <IP> failed"

    def test_ports_replaced(self) -> None:
        assert normalize_error_pattern("listening on :8080") == "listening on :<PORT>"

    def test_uuids_replaced(self) -> None:
        result = normalize_error_pattern("job 123e4567-e89b-12d3-a456-426614174000 failed")
        assert result == "job <UUID> failed"

    def test_paths_replaced(self) -> None:
        result = normalize_error_pattern("failed at /var/log/app.log")
        assert result == "failed at <PATH>"

    def test_numbers_replaced(self) -> None:
        assert normalize_error_pattern("got 42 errors") == "got <NUM> errors"

    def test_hex_replaced(self) -> None:
        assert normalize_error_pattern("pointer 0xdeadbeef freed") == "pointer <HEX> freed"


class TestFilterLinesTzAware:
    """Tests that filter_lines handles timezone-aware and naive timestamps
    the same way cli._parse_file does: naive log entries are compared as-is
    against the (naive) start/end bound, while tz-aware entries are stripped
    to naive for the comparison. This prevents the TypeError that would
    otherwise fire when one side is aware and the other is naive."""

    def test_filter_lines_tz_aware_entry_against_naive_start(self) -> None:
        """A tz-aware entry at 15:00:00+00:00 must not crash when compared
        against a naive start_time of 16:00:00 -- the tz-aware offset is
        dropped to naive so the comparison can happen, and the entry is
        correctly dropped as being before the start bound."""
        lines = ["2025-10-10T15:00:00+00:00 INFO hello"]
        start = datetime(2025, 10, 10, 16, 0, 0)
        results = list(filter_lines(iter(lines), start_time=start))
        assert results == []

    def test_filter_lines_tz_aware_entry_after_naive_start(self) -> None:
        lines = ["2025-10-10T17:00:00+00:00 INFO kept"]
        start = datetime(2025, 10, 10, 16, 0, 0)
        results = list(filter_lines(iter(lines), start_time=start))
        assert len(results) == 1
        assert results[0][1] == "2025-10-10T17:00:00+00:00 INFO kept"
