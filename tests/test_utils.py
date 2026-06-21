"""Tests for log-analyzer-cli utility functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from log_analyzer_cli.utils import (
    _try_parse_datetime,
    detect_log_level,
    parse_timestamp,
)


class TestTryParseDatetime:
    """Tests for _try_parse_datetime."""

    def test_iso_with_microseconds_and_offset_colon(self):
        # Python's datetime.isoformat() emits exactly this form
        assert _try_parse_datetime("2026-06-21T19:25:00.123456+02:00") == datetime(
            2026, 6, 21, 19, 25, 0, 123456,
            tzinfo=timezone(timedelta(hours=2)),
        )

    def test_iso_with_microseconds_and_offset_no_colon(self):
        # ISO 8601 also allows ±HHMM form
        assert _try_parse_datetime("2026-06-21T19:25:00.123456+0200") == datetime(
            2026, 6, 21, 19, 25, 0, 123456,
            tzinfo=timezone(timedelta(hours=2)),
        )

    def test_space_separator_with_microseconds_and_offset(self):
        # The space-separator variant also gets a combined format
        assert _try_parse_datetime("2026-06-21 19:25:00.123456+02:00") == datetime(
            2026, 6, 21, 19, 25, 0, 123456,
            tzinfo=timezone(timedelta(hours=2)),
        )

    def test_iso_microseconds_with_z_suffix(self):
        # Existing Z-substitution should still work for fractional seconds
        assert _try_parse_datetime("2026-06-21T19:25:00.123Z") == datetime(
            2026, 6, 21, 19, 25, 0, 123000,
            tzinfo=timezone.utc,
        )

    def test_iso_microseconds_no_timezone(self):
        # The pre-existing microsecond form must keep working
        assert _try_parse_datetime("2026-06-21T19:25:00.123456") == datetime(
            2026, 6, 21, 19, 25, 0, 123456,
        )

    def test_iso_no_microseconds_with_offset(self):
        # The pre-existing offset form must keep working
        assert _try_parse_datetime("2026-06-21T19:25:00+02:00") == datetime(
            2026, 6, 21, 19, 25, 0,
            tzinfo=timezone(timedelta(hours=2)),
        )

    def test_iso_no_microseconds_no_timezone(self):
        # The pre-existing plain form must keep working
        assert _try_parse_datetime("2026-06-21T19:25:00") == datetime(
            2026, 6, 21, 19, 25, 0,
        )


class TestParseTimestampIntegration:
    """End-to-end checks through parse_timestamp."""

    def test_combined_form_extracts_full_datetime(self):
        # parse_timestamp's first regex captures the whole ISO timestamp;
        # the inner _try_parse_datetime must now handle microseconds+offset.
        assert parse_timestamp(
            "2026-06-21T19:25:00.123456+02:00 ERROR something failed"
        ) == datetime(2026, 6, 21, 19, 25, 0, 123456,
                      tzinfo=timezone(timedelta(hours=2)))

    def test_z_fractional_extracts_full_datetime(self):
        assert parse_timestamp(
            "2026-06-21T19:25:00.123Z ERROR something failed"
        ) == datetime(2026, 6, 21, 19, 25, 0, 123000, tzinfo=timezone.utc)

    def test_plain_form_still_parses(self):
        # regression guard
        assert parse_timestamp("2026-06-21 19:25:00 INFO ok") == datetime(
            2026, 6, 21, 19, 25, 0,
        )


class TestDetectLogLevel:
    def test_returns_uppercase_level(self):
        assert detect_log_level("2025-01-01 error: bad") == "ERROR"

    def test_returns_unknown_for_plain_text(self):
        assert detect_log_level("just a normal line") == "UNKNOWN"
