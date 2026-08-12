"""Tests for log_analyzer_cli.utils timestamp parsing.

The utils module is shared by every parser, so it deserves its own focused
tests. The most important regression here is the syslog-style
"%b %d %H:%M:%S" format, which has no year component — datetime.strptime
fills 1900 as the default, which then propagates through analyze() into
first_seen / last_seen / TimeDistribution and breaks any time-series
report on a syslog file.
"""

from __future__ import annotations

from datetime import datetime

from log_analyzer_cli.utils import parse_timestamp


class TestParseTimestampYearlessFormats:
    """Yearless formats (syslog-style) must be anchored to the current year."""

    def test_syslog_style_timestamp_is_anchored_to_current_year(self):
        # "Mar 20 10:15:32" without a year. Pre-fix this returned 1900-03-20,
        # which then sorted before every other timestamp and made every
        # syslog entry appear in a separate "year 1900" bucket in time
        # distribution reports.
        line = "Mar 20 10:15:32 server1 sshd[1234]: Accepted publickey"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.year == datetime.now().year
        assert ts.month == 3
        assert ts.day == 20
        assert ts.hour == 10
        assert ts.minute == 15
        assert ts.second == 32

    def test_yearless_format_does_not_default_to_1900(self):
        line = "Apr  5 03:14:15 host kernel: oops"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.year != 1900
        assert ts.year == datetime.now().year

    def test_iso_timestamp_keeps_its_own_year(self):
        # Sanity check: the year-fixing logic must not rewrite timestamps
        # that already carry a year. This is the common path for JSON logs
        # and most application logs.
        line = "2024-07-15T08:30:00Z something happened"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.year == 2024
        assert ts.month == 7
        assert ts.day == 15


class TestParseTimestampNoTimestamp:
    """Lines without a timestamp must return None, not crash."""

    def test_line_with_no_timestamp_returns_none(self):
        ts = parse_timestamp("just a plain line with no date at all")
        assert ts is None

    def test_empty_string_returns_none(self):
        ts = parse_timestamp("")
        assert ts is None

    def test_only_whitespace_returns_none(self):
        ts = parse_timestamp("   \t  ")
        assert ts is None


class TestParseTimestampYearlessEdgeCases:
    """Edge cases for the year-fill logic."""

    def test_single_digit_day_is_parsed(self):
        # RFC 3164 syslog timestamps use %b %-d (single-digit day, no
        # zero-padding). "Mar  5" with two spaces between month and day
        # must still parse.
        line = "Mar  5 03:14:15 host kernel: oops"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.day == 5
        assert ts.year == datetime.now().year