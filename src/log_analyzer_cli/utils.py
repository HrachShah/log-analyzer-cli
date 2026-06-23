"""Utility functions for log-analyzer-cli."""

from __future__ import annotations

import gzip
import re
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional


def parse_timestamp(line: str) -> Optional[datetime]:
    """Parse timestamp from a log line.
    
    Args:
        line: A log line that may contain a timestamp.
        
    Returns:
        Parsed datetime object or None if no timestamp found.
    """
    timestamp_patterns = [
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
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

    # Replace full URLs (with scheme) as a single unit, BEFORE hostname /
    # path replacements run — otherwise a URL like https://api.example.com/foo
    # is broken into "https:" + "/api.example.com/foo", the hostname matcher
    # (which requires the host to be a single word before a known TLD) misses
    # "api.example.com" because "api" is preceded by "/", and the path
    # matcher swallows everything to end-of-line. Result: "https:<PATH>".
    pattern = re.sub(r'\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s]+', '<URL>', pattern)

    # Replace IPv6 addresses (with or without embedded ::) before the IPv4 /
    # port rules fire, since IPv6 contains ':' but is not a "host:port".
    pattern = re.sub(
        r'\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b', '<IPV6>', pattern
    )

    # Replace IP:port combinations first
    pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', '<IP>', pattern)
    
    # Replace plain IP addresses
    pattern = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', pattern)
    
    # Replace hostnames: support multi-segment domains (e.g. api.example.com)
    # as well as single-label hostnames ending in a known TLD. The
    # single-segment pattern matched only "host.tld" and silently dropped
    # deeper hostnames, so api.example.com leaked through to the path rule.
    pattern = re.sub(
        r'\b(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+'
        r'(?:local|com|net|org|io|dev|co|uk|gov|edu|info|biz|us|me|app|ai)\b',
        '<HOST>',
        pattern,
    )
    pattern = re.sub(r'\blocalhost\b', '<HOST>', pattern)
    
    # Replace port numbers (after IP and host replacement)
    pattern = re.sub(r':\d+', ':<PORT>', pattern)
    
    # Replace UUIDs
    pattern = re.sub(
        r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>', pattern
    )
    
    # Replace paths (only "/" or "./" or "../" relative paths, not the trailing
    # slash of a URL that was already collapsed to <URL>).
    pattern = re.sub(r'(?:^|[\s(=])\.{0,2}/[^\s]+', lambda m: m.group(0)[0] + '<PATH>', pattern)
    
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
        
        if start_time and timestamp and timestamp < start_time:
            continue
        
        if end_time and timestamp and timestamp > end_time:
            continue
        
        yield line_num, line, timestamp, level
