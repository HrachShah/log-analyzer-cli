"""Tests for log analyzer timestamp utilities."""

from datetime import datetime, timezone

from log_analyzer_cli.utils import filter_lines, parse_timestamp


def test_filter_lines_compares_mixed_timestamp_awareness():
    lines = iter([
        "2026-04-20 10:29:59 INFO before",
        "2026-04-20T10:30:00Z INFO naive boundary match",
        "2026-04-20 10:30:01 INFO aware boundary match",
    ])
    boundary = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)

    filtered = list(filter_lines(lines, start_time=boundary))

    assert [line for _, line, _, _ in filtered] == [
        "2026-04-20T10:30:00Z INFO naive boundary match",
        "2026-04-20 10:30:01 INFO aware boundary match",
    ]


def test_parse_timestamp_accepts_slash_separated_iso_timestamp():
    parsed = parse_timestamp("2026/04/20 10:30:00 INFO started")

    assert parsed == datetime(2026, 4, 20, 10, 30, 0)


def test_time_filters_exclude_entries_without_timestamps():
    lines = iter([
        "INFO no timestamp",
        "2026-04-20 10:30:00 INFO timestamped",
    ])
    boundary = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)

    filtered = list(filter_lines(lines, start_time=boundary, end_time=boundary))

    assert [line for _, line, _, _ in filtered] == [
        "2026-04-20 10:30:00 INFO timestamped",
    ]


def test_parse_timestamp_accepts_space_separated_timezone_offset():
    parsed = parse_timestamp("2026-04-20 10:30:00+02:00 INFO started")

    assert parsed == datetime.fromisoformat("2026-04-20T10:30:00+02:00")


def test_parse_timestamp_accepts_space_separated_fractional_offset():
    parsed = parse_timestamp("2026-04-20 10:30:00.125-0500 INFO started")

    assert parsed == datetime.fromisoformat("2026-04-20T10:30:00.125-05:00")
