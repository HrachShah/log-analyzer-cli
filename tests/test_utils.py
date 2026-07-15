"""Tests for log_analyzer_cli.utils helpers.

Targets the ``filter_lines`` boundary in particular: a user with a
syslog line that is tz-naive (no offset in the timestamp) and a
``--start-time`` argument parsed by Click that *is* tz-aware should
not crash with ``TypeError: can't compare offset-naive and
offset-aware datetimes``. The same is true in reverse for a
tz-aware line against a naive bound, which is the case the existing
CLI codepath already handles in ``cli._parse_file``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from log_analyzer_cli.utils import filter_lines, parse_timestamp


class TestFilterLinesTzAware:
    """Cover the tz-naive-vs-tz-aware comparison edges of ``filter_lines``."""

    def test_naive_entry_against_tz_aware_start_does_not_raise(self) -> None:
        """A naive log line (no offset) against a tz-aware ``--start-time``
        used to raise ``TypeError`` because Python's ``<`` between a
        naive ``datetime`` and an aware one is undefined. The fix
        normalises the aware bound to naive so the comparison is
        well-defined and the line is kept (it is past the bound)."""
        lines = iter(["2025-10-10T17:00:00 INFO kept"])
        start = datetime(2025, 10, 10, 16, 0, tzinfo=timezone.utc)
        results = list(filter_lines(lines, start_time=start))
        assert len(results) == 1
        line_num, line, timestamp, level = results[0]
        assert line_num == 1
        assert "INFO kept" in line
        assert timestamp == datetime(2025, 10, 10, 17, 0)
        assert timestamp.tzinfo is None
        assert level == "INFO"

    def test_naive_entry_against_tz_aware_start_below_bound_is_dropped(self) -> None:
        """A naive log line below a tz-aware ``--start-time`` is dropped
        rather than crashing; the bound is normalised to naive so the
        comparison can proceed."""
        lines = iter(["2025-10-10T15:00:00 INFO dropped"])
        start = datetime(2025, 10, 10, 16, 0, tzinfo=timezone.utc)
        results = list(filter_lines(lines, start_time=start))
        assert results == []

    def test_naive_entry_against_tz_aware_end_is_dropped(self) -> None:
        """Same symmetry on the end-bound side: a naive entry past a
        tz-aware ``--end-time`` is dropped without raising."""
        lines = iter(["2025-10-10T15:00:00 INFO dropped"])
        end = datetime(2025, 10, 10, 14, 0, tzinfo=timezone.utc)
        results = list(filter_lines(lines, end_time=end))
        assert results == []

    def test_tz_aware_entry_against_naive_start_kept(self) -> None:
        """The reverse case (tz-aware log entry, tz-naive bound), which
        the in-tree ``cli._parse_file`` codepath already handles, is
        exercised end-to-end through ``filter_lines`` to make sure the
        helper, the CLI, and direct library callers all agree."""
        lines = iter(["2025-10-10T17:00:00+00:00 INFO kept"])
        start = datetime(2025, 10, 10, 16, 0)
        results = list(filter_lines(lines, start_time=start))
        assert len(results) == 1
        line_num, line, timestamp, level = results[0]
        assert timestamp.tzinfo is not None
        assert timestamp.utcoffset().total_seconds() == 0
        assert level == "INFO"

    def test_tz_aware_entry_against_tz_aware_start_both_drop_tz(self) -> None:
        """When both sides are tz-aware, the helper still drops tzinfo
        before comparing, matching the existing contract: log-line tz
        is preserved in the yielded entry, but is stripped from the
        compare-time value so the comparison itself stays simple."""
        lines = iter(["2025-10-10T17:00:00+05:00 INFO kept"])
        start = datetime(2025, 10, 10, 16, 0, tzinfo=timezone.utc)
        results = list(filter_lines(lines, start_time=start))
        assert len(results) == 1
        _, _, timestamp, _ = results[0]
        assert timestamp.tzinfo is not None
        assert timestamp.utcoffset().total_seconds() == 5 * 3600

    def test_naive_entry_no_bounds_returns_all(self) -> None:
        """Sanity check: no bounds means no comparison, every line is
        yielded. Catches accidental over-normalisation where the
        helper might start dropping lines it should keep."""
        lines = iter(
            [
                "2025-10-10T17:00:00 INFO first",
                "2025-10-10T18:00:00+00:00 INFO second",
            ]
        )
        results = list(filter_lines(lines))
        assert len(results) == 2


class TestNormalizeErrorPattern:
    """Cover ordering-sensitive replacements in error grouping."""

    def test_hex_values_are_not_partially_replaced_as_numbers(self) -> None:
        from log_analyzer_cli.utils import normalize_error_pattern

        assert normalize_error_pattern("invalid token 0xDEAD1234") == "invalid token <HEX>"
