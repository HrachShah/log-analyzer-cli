"""Tests for log_analyzer_cli.utils.

Pins behaviour for cross-tz comparisons between parsed log timestamps and
CLI-supplied start/end time filters. A log file may contain both naive
timestamps (e.g. ``2025-03-20 10:15:32`` from syslog) and tz-aware ones
(e.g. ``2025-03-20T10:15:32+00:00`` from JSON). Python raises TypeError
when comparing naive and aware datetimes, so the comparison path has to
normalise both sides before the inequality check.
"""

from datetime import datetime, timezone

from log_analyzer_cli.utils import _align_datetime_to_filter, filter_lines


class TestAlignDatetimeToFilter:
    """Verify the helper that bridges naive/aware datetime comparisons."""

    def test_none_input_returns_none(self):
        assert _align_datetime_to_filter(None) is None
        assert _align_datetime_to_filter(None, start_time=datetime(2025, 1, 1)) is None

    def test_naive_in_naive_naive_returns_naive(self):
        ts = datetime(2025, 3, 20, 10, 15, 32)
        start = datetime(2025, 1, 1, 0, 0, 0)
        end = datetime(2025, 12, 31, 23, 59, 59)
        assert _align_datetime_to_filter(ts, start_time=start, end_time=end) is ts

    def test_aware_in_naive_filter_strips_tzinfo(self):
        ts = datetime(2025, 3, 20, 10, 15, 32, tzinfo=timezone.utc)
        start = datetime(2025, 1, 1, 0, 0, 0)  # naive
        result = _align_datetime_to_filter(ts, start_time=start)
        assert result.tzinfo is None
        assert result == ts.replace(tzinfo=None)

    def test_aware_in_aware_filter_is_unchanged(self):
        ts = datetime(2025, 3, 20, 10, 15, 32, tzinfo=timezone.utc)
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = _align_datetime_to_filter(ts, start_time=start)
        assert result.tzinfo is timezone.utc
        assert result == ts

    def test_naive_in_aware_filter_attaches_utc(self):
        ts = datetime(2025, 3, 20, 10, 15, 32)  # naive
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = _align_datetime_to_filter(ts, start_time=start)
        assert result.tzinfo is timezone.utc
        assert result == ts.replace(tzinfo=timezone.utc)

    def test_end_time_naive_strips_aware_timestamp(self):
        ts = datetime(2025, 3, 20, 10, 15, 32, tzinfo=timezone.utc)
        end = datetime(2025, 12, 31, 23, 59, 59)  # naive
        result = _align_datetime_to_filter(ts, end_time=end)
        assert result.tzinfo is None


class TestFilterLinesTimezone:
    """End-to-end checks that filter_lines never raises on tz mismatch."""

    def test_aware_start_does_not_crash_on_naive_log(self):
        # Simulates the bug: parsed log is naive, start_time is aware.
        lines = iter(["2025-01-01 10:00:00 INFO test entry"])
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        # Should not raise.
        result = list(filter_lines(lines, start_time=start))
        assert len(result) == 1
        # The yielded timestamp is normalised to UTC for the aware filter.
        assert result[0][2].tzinfo is timezone.utc

    def test_naive_start_does_not_crash_on_aware_log(self):
        lines = iter(["2025-01-01T10:00:00+00:00 INFO test entry"])
        start = datetime(2025, 1, 1, 0, 0, 0)  # naive
        # Should not raise.
        result = list(filter_lines(lines, start_time=start))
        assert len(result) == 1
        # The yielded timestamp is normalised to naive for the naive filter.
        assert result[0][2].tzinfo is None

    def test_excludes_entries_before_aware_start(self):
        lines = iter([
            "2024-12-31T23:59:59+00:00 INFO too early",
            "2025-01-02T10:00:00+00:00 INFO inside window",
        ])
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = list(filter_lines(lines, start_time=start))
        assert len(result) == 1
        assert "inside window" in result[0][1]
    def test_mixed_filter_boundaries_use_one_timezone(self):
        lines = iter(["2025-01-01T12:00:00+00:00 INFO inside window"])
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 1, 2, 0, 0, 0)
        result = list(filter_lines(lines, start_time=start, end_time=end))
        assert len(result) == 1

def test_normalize_error_pattern_keeps_hex_values_together():
    from log_analyzer_cli.utils import normalize_error_pattern

    assert normalize_error_pattern("invalid value 0xDEADBEEF") == "invalid value <HEX>"


def test_parse_timestamp_accepts_space_before_timezone_offset():
    from log_analyzer_cli.utils import parse_timestamp

    timestamp = parse_timestamp("2025-03-20 10:15:32+02:00 INFO started")

    assert timestamp is not None
    assert timestamp.isoformat() == "2025-03-20T10:15:32+02:00"


def test_parse_timestamp_preserves_fractional_seconds_with_timezone():
    from log_analyzer_cli.utils import parse_timestamp

    timestamp = parse_timestamp("2025-03-20T10:15:32.123Z INFO started")

    assert timestamp is not None
    assert timestamp.isoformat() == "2025-03-20T10:15:32.123000+00:00"
