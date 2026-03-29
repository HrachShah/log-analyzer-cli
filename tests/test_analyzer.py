"""Tests for log analyzer."""

from __future__ import annotations

from datetime import datetime

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
    
    def test_reset(self):
        analyzer = LogAnalyzer()
        entries = [
            ParsedEntry(raw="Error", level="ERROR", message="Error"),
        ]
        
        analyzer.analyze(entries)
        assert len(analyzer._error_patterns) > 0
        
        analyzer.reset()
        assert len(analyzer._error_patterns) == 0


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
