from datetime import datetime, timezone

from log_analyzer_cli.utils import filter_lines, normalize_error_pattern, parse_timestamp


def test_parse_timestamp_accepts_space_before_timezone_offset():
    assert parse_timestamp("2025-03-20 10:00:01+01:00").isoformat() == "2025-03-20T10:00:01+01:00"


def test_filter_lines_compares_aware_timestamp_with_naive_bounds():
    lines = iter(["2025-03-20T09:00:00+00:00 INFO early\n", "2025-03-20T11:00:00+00:00 INFO late\n"])

    result = list(filter_lines(lines, start_time=datetime(2025, 3, 20, 10)))

    assert [line for _, line, _, _ in result] == ["2025-03-20T11:00:00+00:00 INFO late"]


def test_filter_lines_compares_naive_timestamp_with_aware_bounds():
    lines = iter(["2025-03-20T09:00:00 INFO early\n", "2025-03-20T11:00:00 INFO late\n"])

    result = list(
        filter_lines(
            lines,
            end_time=datetime(2025, 3, 20, 10, tzinfo=timezone.utc),
        )
    )

    assert [line for _, line, _, _ in result] == ["2025-03-20T09:00:00 INFO early"]




def test_normalize_hex_values_as_single_placeholders():
    assert normalize_error_pattern("status 0x404") == "status <HEX>"
