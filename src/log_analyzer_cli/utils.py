"""Utility functions for log-analyzer-cli."""

from __future__ import annotations

import gzip
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional


def _normalise_datetime_pair(
    timestamp: datetime, boundary: datetime
) -> tuple[datetime, datetime]:
    """Make a timestamp and filter boundary comparable.

    Naive timestamps are interpreted as UTC whenever either value carries
    timezone information. This avoids Python's TypeError for mixed-aware
    comparisons without silently discarding an offset from a parsed log.
    """
    if timestamp.tzinfo is None and boundary.tzinfo is None:
        return timestamp, boundary

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if boundary.tzinfo is None:
        boundary = boundary.replace(tzinfo=timezone.utc)
    return timestamp, boundary


def parse_timestamp(line: str) -> Optional[datetime]:
    """Parse timestamp from a log line.
    
    Args:
        line: A log line that may contain a timestamp.
        
    Returns:
        Parsed datetime object or None if no timestamp found.
    """
    timestamp_patterns = [
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\s*[+-]\d{2}:?\d{2})?",
        r"\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}",
        r"[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}",
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, line)
        if match:
            ts_str = match.group()
            parsed = _try_parse_datetime(ts_str)
            if parsed:
                return parsed
    return None


def _try_parse_datetime(ts_str: str) -> Optional[datetime]:
    """Try to parse a datetime string with various formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f %z",
        "%Y-%m-%d %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%d/%b/%Y:%H:%M:%S",
        "%b %d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return None


def read_log_file(file_path: str | Path) -> Generator[str, None]:
    """Read a log file, handling gzip compression.
    
    Args:
        file_path: Path to the log file.
        
    Yields:
        Lines from the log file.
    """
    path = Path(file_path)
    
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            yield from f
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            yield from f


def normalize_error_pattern(error_msg: str) -> str:
    """Normalize an error message for grouping similar errors.
    
    Replaces specific values like numbers, UUIDs, paths with placeholders.
    
    Args:
        error_msg: The error message to normalize.
        
    Returns:
        Normalized pattern string.
    """
    pattern = error_msg
    
    # Replace IP:port combinations first
    pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', '<IP>', pattern)
    
    # Replace plain IP addresses
    pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', pattern)
    
    # Replace hostnames (domain-like patterns)
    pattern = re.sub(r'\b[a-zA-Z0-9][-a-zA-Z0-9]*\.(local|com|net|org|io|dev)\b', '<HOST>', pattern)
    pattern = re.sub(r'\blocalhost\b', '<HOST>', pattern)
    
    # Replace port numbers (after IP and host replacement)
    pattern = re.sub(r':\d+', ':<PORT>', pattern)
    
    # Replace UUIDs
    pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>', pattern)
    
    # Replace paths
    pattern = re.sub(r'/[^\s]+', '<PATH>', pattern)
    
    # Replace remaining standalone numbers
    pattern = re.sub(r'\b\d+\b', '<NUM>', pattern)
    
    # Replace hex values
    pattern = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', pattern)
    
    return pattern


def detect_log_level(line: str) -> str:
    """Detect log level from a log line.
    
    Args:
        line: A log line.
        
    Returns:
        The detected log level (ERROR, WARNING, INFO, DEBUG, CRITICAL, UNKNOWN).
    """
    line_upper = line.upper()
    
    level_patterns = [
        (r'\bCRITICAL\b|\bCRIT\b', "CRITICAL"),
        (r'\bERROR\b|\bERR\b', "ERROR"),
        (r'\bWARNING\b|\bWARN\b', "WARNING"),
        (r'\bINFO\b', "INFO"),
        (r'\bDEBUG\b|\bDBG\b', "DEBUG"),
        (r'\bTRACE\b|\bTRC\b', "TRACE"),
    ]
    
    for pattern, level in level_patterns:
        if re.search(pattern, line_upper):
            return level
    
    return "UNKNOWN"


def filter_lines(
    lines: Generator[str, None, None],
    include_levels: Optional[list[str]] = None,
    exclude_levels: Optional[list[str]] = None,
    search_pattern: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Generator[tuple[int, str, Optional[datetime], str], None]:
    """Filter log lines based on various criteria.
    
    Args:
        lines: Iterator of log lines.
        include_levels: List of log levels to include.
        exclude_levels: List of log levels to exclude.
        search_pattern: Regex pattern to search for.
        start_time: Only include entries after this time.
        end_time: Only include entries before this time.
        
    Yields:
        Tuples of (line_number, line, timestamp, level).
    """
    compiled_pattern = re.compile(search_pattern) if search_pattern else None
    
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip("\n\r")
        if not line:
            continue
        
        level = detect_log_level(line)
        
        if include_levels and level not in include_levels:
            continue
        
        if exclude_levels and level in exclude_levels:
            continue
        
        if compiled_pattern and not compiled_pattern.search(line):
            continue
        
        timestamp = parse_timestamp(line)

        if timestamp is not None and start_time is not None:
            comparable_timestamp, comparable_start = _normalise_datetime_pair(
                timestamp, start_time
            )
            if comparable_timestamp < comparable_start:
                continue

        if timestamp is not None and end_time is not None:
            comparable_timestamp, comparable_end = _normalise_datetime_pair(timestamp, end_time)
            if comparable_timestamp > comparable_end:
                continue
        
        yield line_num, line, timestamp, level
