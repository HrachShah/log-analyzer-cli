"""Tests for utility functions."""

from __future__ import annotations

from log_analyzer_cli.utils import _try_parse_datetime, parse_timestamp


class TestTryParseDatetime:
    """Tests for _try_parse_datetime and the format list it walks."""

    def test_microseconds_with_z_suffix(self):
        # 'Z' is rewritten to '+00:00' before strptime, so the combined
        # microsecond+timezone format must be in the list.
        result = _try_parse_datetime("2025-03-20T10:15:32.123Z")
        assert result is not None
        assert result.year == 2025
        assert result.microsecond == 123000
        assert result.utcoffset().total_seconds() == 0

    def test_microseconds_with_space_separator_and_tz(self):
        result = _try_parse_datetime("2025-03-20 10:15:32.456+00:00")
        assert result is not None
        assert result.microsecond == 456000

    def test_microseconds_with_positive_offset(self):
        result = _try_parse_datetime("2025-03-20T10:15:32.123+05:30")
        assert result is not None
        assert result.utcoffset().total_seconds() == 5 * 3600 + 30 * 60

    def test_no_microseconds_with_z_suffix(self):
        # The non-microsecond + timezone format was already present.
        result = _try_parse_datetime("2025-03-20T10:15:32Z")
        assert result is not None
        assert result.utcoffset().total_seconds() == 0

    def test_plain_datetime_still_parses(self):
        result = _try_parse_datetime("2025-03-20 10:15:32")
        assert result is not None
        assert result == _try_parse_datetime("2025-03-20 10:15:32")

    def test_unparseable_returns_none(self):
        assert _try_parse_datetime("not a date at all") is None


class TestParseTimestamp:
    """Tests for parse_timestamp on full log lines."""

    def test_iso_with_milliseconds_in_json_line(self):
        # This is the regression that motivated the fix.
        line = '{"timestamp": "2025-03-20T10:15:32.123Z", "message": "x"}'
        result = parse_timestamp(line)
        assert result is not None
        assert result.microsecond == 123000

    def test_iso_with_milliseconds_and_offset(self):
        line = '{"time": "2025-03-20 10:15:32.456+00:00", "message": "x"}'
        result = parse_timestamp(line)
        assert result is not None
        assert result.microsecond == 456000
