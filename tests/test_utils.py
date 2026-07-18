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
