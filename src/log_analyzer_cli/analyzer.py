"""Core analysis logic for log-analyzer-cli."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from log_analyzer_cli.parsers import ParsedEntry
from log_analyzer_cli.utils import normalize_error_pattern


@dataclass
class LogEntry:
    """A log entry with analyzed data."""
    line_number: int
    raw: str
    timestamp: Optional[datetime] = None
    level: str = "UNKNOWN"
    message: str = ""
    source: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ErrorGroup:
    """A group of similar errors."""
    pattern: str
    count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    sample_messages: list[str] = field(default_factory=list)


@dataclass
class TimeDistribution:
    """Distribution of log entries over time."""
    entries: list[datetime] = field(default_factory=list)
    interval_minutes: int = 60


@dataclass
class AnalysisResult:
    """Result of log analysis."""
    total_lines: int = 0
    parsed_entries: int = 0
    level_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_groups: list[ErrorGroup] = field(default_factory=list)
    time_distribution: Optional[TimeDistribution] = None
    source_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    warnings: list[str] = field(default_factory=list)
    parse_errors: int = 0


class LogAnalyzer:
    """Analyzer for log files."""
    
    def __init__(self, max_error_group_samples: int = 5):
        self.max_error_group_samples = max_error_group_samples
        self._error_patterns: dict[str, ErrorGroup] = {}
    
    def analyze(
        self,
        entries: list[ParsedEntry],
        group_errors: bool = True,
    ) -> AnalysisResult:
        """Analyze a list of parsed log entries.
        
        Args:
            entries: List of parsed log entries.
            group_errors: Whether to group similar errors.
            
        Returns:
            Analysis result.
        """
        result = AnalysisResult()
        result.total_lines = len(entries)
        result.parsed_entries = len(entries)
        
        timestamps = []
        
        for entry in entries:
            result.level_counts[entry.level] += 1
            
            if entry.source:
                result.source_counts[entry.source] += 1
            
            if entry.timestamp:
                timestamps.append(entry.timestamp)
            
            if group_errors and entry.level in ("ERROR", "CRITICAL", "WARNING"):
                self._add_to_error_group(entry)
        
        if timestamps:
            result.time_distribution = TimeDistribution(
                entries=sorted(timestamps),
                interval_minutes=60,
            )
        
        if group_errors:
            result.error_groups = sorted(
                self._error_patterns.values(),
                key=lambda g: g.count,
                reverse=True,
            )
        
        return result
    
    def _add_to_error_group(self, entry: ParsedEntry) -> None:
        """Add an entry to an error group."""
        if not entry.message:
            pattern = normalize_error_pattern(entry.raw)
        else:
            pattern = normalize_error_pattern(entry.message)
        
        if pattern not in self._error_patterns:
            self._error_patterns[pattern] = ErrorGroup(pattern=pattern)
        
        group = self._error_patterns[pattern]
        group.count += 1
        
        if entry.timestamp:
            if group.first_seen is None or entry.timestamp < group.first_seen:
                group.first_seen = entry.timestamp
            if group.last_seen is None or entry.timestamp > group.last_seen:
                group.last_seen = entry.timestamp
        
        if len(group.sample_messages) < self.max_error_group_samples:
            if entry.message:
                sample = entry.message
            else:
                sample = entry.raw[:200]
            if sample not in group.sample_messages:
                group.sample_messages.append(sample)
    
    def reset(self) -> None:
        """Reset the analyzer state."""
        self._error_patterns = {}


def analyze_log_entries(
    entries: list[ParsedEntry],
    group_errors: bool = True,
) -> AnalysisResult:
    """Analyze log entries and return results.
    
    Args:
        entries: List of parsed log entries.
        group_errors: Whether to group similar errors.
        
    Returns:
        Analysis result.
    """
    analyzer = LogAnalyzer()
    return analyzer.analyze(entries, group_errors)
