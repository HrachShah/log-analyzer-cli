from datetime import datetime, timezone

from log_analyzer_cli.utils import filter_lines


def test_filter_lines_compares_aware_entries_with_naive_bounds():
    result = list(filter_lines(
        iter(["2025-03-20T10:15:32.123Z host process: message"]),
        start_time=datetime(2025, 3, 20, 10, 15, 32),
    ))
    assert len(result) == 1


def test_filter_lines_compares_naive_entries_with_aware_bounds():
    result = list(filter_lines(
        iter(["2025-03-20 10:15:32 host process: message"]),
        end_time=datetime(2025, 3, 20, 10, 15, 32, tzinfo=timezone.utc),
    ))
    assert len(result) == 1


def test_filter_lines_preserves_aware_timestamp_instant_for_naive_bounds():
    result = list(filter_lines(
        iter(["2025-03-20T10:15:32+02:00 host process: message"]),
        end_time=datetime(2025, 3, 20, 8, 0, 0),
    ))
    assert len(result) == 0


def test_normalize_error_pattern_keeps_hex_values_as_hex_placeholders():
    from log_analyzer_cli.utils import normalize_error_pattern

    assert normalize_error_pattern("checksum mismatch at 0xdeadbeef") == "checksum mismatch at <HEX>"
