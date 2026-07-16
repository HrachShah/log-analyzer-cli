"""Tests for log analyzer."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from log_analyzer_cli.analyzer import ErrorGroup, LogAnalyzer, analyze_log_entries
from log_analyzer_cli.parsers import ParsedEntry


class TestLogAnalyzer:
    """Tests for LogAnalyzer."""
    
    def test_analyze_empty_entries(self):
        analyzer = LogAnalyzer()
        result = analyzer.analyze([])
        
        assert result.total_lines == 0
        assert result.parsed_entries == 0
        assert len(result.level_counts) == 0
    
    def test_analyze_single_entry(self):
        analyzer = LogAnalyzer()
        entry = ParsedEntry(
            raw="Test log line",
            timestamp=datetime(2025, 3, 20, 10, 15, 32),
            level="INFO",
            message="Test message",
        )
        
        result = analyzer.analyze([entry])
        
        assert result.total_lines == 1
        assert result.parsed_entries == 1
        assert result.level_counts["INFO"] == 1
    
    def test_analyze_multiple_levels(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Error 1", level="ERROR", message="Error 1"),
            ParsedEntry(raw="Error 2", level="ERROR", message="Error 2"),
            ParsedEntry(raw="Warning 1", level="WARNING", message="Warning 1"),
            ParsedEntry(raw="Info 1", level="INFO", message="Info 1"),
        ]
        
        result = analyzer.analyze(entries)
        
        assert result.level_counts["ERROR"] == 2
        assert result.level_counts["WARNING"] == 1
        assert result.level_counts["INFO"] == 1
    
    def test_error_grouping(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(
                raw="Error: Connection failed to database server at localhost:5432",
                level="ERROR",
                message="Connection failed to database server at localhost:5432",
            ),
            ParsedEntry(
                raw="Error: Connection failed to database server at dbserver.local:5432",
                level="ERROR",
                message="Connection failed to database server at dbserver.local:5432",
            ),
            ParsedEntry(
                raw="Error: Connection failed to database server at redis.local:6379",
                level="ERROR",
                message="Connection failed to database server at redis.local:6379",
            ),
        ]
        
        result = analyzer.analyze(entries, group_errors=True)
        
        assert len(result.error_groups) > 0
        assert result.error_groups[0].count == 3
    
    def test_error_grouping_similar_messages(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Error: timeout after 30s", level="ERROR", message="timeout after 30s"),
            ParsedEntry(raw="Error: timeout after 45s", level="ERROR", message="timeout after 45s"),
            ParsedEntry(raw="Error: timeout after 60s", level="ERROR", message="timeout after 60s"),
        ]
        
        result = analyzer.analyze(entries, group_errors=True)
        
        assert len(result.error_groups) >= 1
    
    def test_no_error_grouping_when_disabled(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Error 1", level="ERROR", message="Error 1"),
            ParsedEntry(raw="Error 2", level="ERROR", message="Error 2"),
        ]
        
        result = analyzer.analyze(entries, group_errors=False)
        
        assert len(result.error_groups) == 0
    
    def test_source_counting(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Log 1", level="INFO", source="apache"),
            ParsedEntry(raw="Log 2", level="INFO", source="apache"),
            ParsedEntry(raw="Log 3", level="INFO", source="nginx"),
        ]
        
        result = analyzer.analyze(entries)
        
        assert result.source_counts["apache"] == 2
        assert result.source_counts["nginx"] == 1
    
    def test_time_distribution(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(
                raw="Log 1",
                level="INFO",
                timestamp=datetime(2025, 3, 20, 10, 15, 0),
            ),
            ParsedEntry(
                raw="Log 2",
                level="INFO",
                timestamp=datetime(2025, 3, 20, 10, 30, 0),
            ),
            ParsedEntry(
                raw="Log 3",
                level="INFO",
                timestamp=datetime(2025, 3, 20, 11, 0, 0),
            ),
        ]
        
        result = analyzer.analyze(entries)
        
        assert result.time_distribution is not None
        assert len(result.time_distribution.entries) == 3
    
    def test_analyze_does_not_reuse_error_groups(self):
        analyzer = LogAnalyzer()

        analyzer.analyze([
            ParsedEntry(raw="Error 1", level="ERROR", message="Error 1"),
        ])
        result = analyzer.analyze([
            ParsedEntry(raw="Info 1", level="INFO", message="Info 1"),
        ])

        assert result.error_groups == []

    def test_reset(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Error", level="ERROR", message="Error"),
        ]
        
        analyzer.analyze(entries)
        assert len(analyzer._error_patterns) > 0
        
        analyzer.reset()
        assert len(analyzer._error_patterns) == 0

    def test_mixed_naive_and_aware_timestamps(self):
        """A single log file can carry both naive and tz-aware timestamps.

        The previous code fed the raw ``entry.timestamp`` values to ``sorted``,
        ``min``/``max``, and ``<``/``>`` comparisons. Python rejects comparing
        offset-naive and offset-aware datetimes with ``TypeError: can't
        compare offset-naive and offset-aware datetimes``, which crashed
        ``TimeDistribution`` construction and error-group first/last_seen
        computation. The fix normalizes a local copy of every timestamp to a
        common tz-awareness (UTC for naive baselines) before sorting or
        comparing, while leaving the original ``entry.timestamp`` on each
        ``ParsedEntry`` untouched.
        """
        from log_analyzer_cli.analyzer import _normalize_timestamp

        naive = datetime(2026, 4, 20, 10, 30, 0)
        aware = datetime(2026, 4, 20, 10, 30, 5, tzinfo=timezone.utc)

        # Sorted: should not raise, and the naive value should be promoted
        # to UTC, not reordered behind the aware one
        assert sorted([aware, naive], key=_normalize_timestamp) == [naive, aware]

        # Min/max: same
        assert min([aware, naive], key=_normalize_timestamp) == naive
        assert max([aware, naive], key=_normalize_timestamp) == aware

        # Time distribution on a mix: should not raise
        entries = [
            ParsedEntry(raw="naive line", timestamp=naive, level="INFO", message="naive"),
            ParsedEntry(raw="aware line", timestamp=aware, level="INFO", message="aware"),
        ]
        result = LogAnalyzer().analyze(entries)
        assert result.time_distribution is not None
        assert len(result.time_distribution.entries) == 2
        # The first entry should still be the naive one (UTC-promoted),
        # proving the sort key honored the original order
        assert result.time_distribution.entries[0] == naive.replace(tzinfo=timezone.utc)
        assert result.time_distribution.entries[1] == aware

        # Error grouping first/last_seen: should not raise
        err_entries = [
            ParsedEntry(raw="Error foo 1", timestamp=naive, level="ERROR", message="Error foo 1"),
            ParsedEntry(raw="Error foo 2", timestamp=aware, level="ERROR", message="Error foo 2"),
        ]
        result = LogAnalyzer().analyze(err_entries, group_errors=True)
        assert len(result.error_groups) == 1
        group = result.error_groups[0]
        assert group.first_seen == naive
        assert group.last_seen == aware


class TestAnalyzeLogEntries:
    """Tests for the analyze_log_entries function."""
    
    def test_convenience_function(self):
        entries = [
            ParsedEntry(raw="Info", level="INFO", message="Test"),
        ]
        
        result = analyze_log_entries(entries)
        
        assert result.parsed_entries == 1
        assert result.level_counts["INFO"] == 1


class TestErrorGroup:
    """Tests for ErrorGroup dataclass."""
    
    def test_error_group_creation(self):
        group = ErrorGroup(pattern="Test pattern", count=5)
        
        assert group.pattern == "Test pattern"
        assert group.count == 5
        assert group.first_seen is None
        assert group.last_seen is None
        assert len(group.sample_messages) == 0
