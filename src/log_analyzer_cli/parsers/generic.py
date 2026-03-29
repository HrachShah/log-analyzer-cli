"""Generic timestamp-based log parser."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from log_analyzer_cli.parsers.base import LogParser, ParsedEntry
from log_analyzer_cli.utils import detect_log_level


class GenericParser(LogParser):
    """Parser for generic log formats with timestamps.
    
    Handles various timestamp-based log formats that don't match
    more specific parsers.
    """
    
    name = "generic"
    description = "Generic timestamp-based log parser"
    
    TIMESTAMP_REGEX = re.compile(
        r'(?P<timestamp>'
        r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?|'
        r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+\w+|'
        r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|'
        r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}|'
        r'\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}'
        r')'
    )
    
    def can_parse(self, line: str) -> bool:
        """Check if line has a recognizable timestamp."""
        return bool(self.TIMESTAMP_REGEX.search(line))
    
    def parse(self, line: str) -> Optional[ParsedEntry]:
        """Parse a generic log line."""
        match = self.TIMESTAMP_REGEX.search(line)
        if not match:
            return None
        
        timestamp = self._parse_timestamp(match.group("timestamp"))
        level = detect_log_level(line)
        
        message_start = match.end()
        message = line[message_start:].strip()
        
        message = re.sub(r'^\s*[-:]\s*', '', message)
        
        return ParsedEntry(
            raw=line,
            timestamp=timestamp,
            level=level,
            message=message,
            metadata={"format": "generic"},
        )
    
    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parse timestamp string."""
        if not ts_str:
            return None
        
        year = datetime.now().year
        
        formats = [
            ("%Y-%m-%d %H:%M:%S.%f", False),
            ("%Y-%m-%dT%H:%M:%S.%f", False),
            ("%Y-%m-%d %H:%M:%S", False),
            ("%Y-%m-%dT%H:%M:%S", False),
            ("%Y-%m-%dT%H:%M:%S.%f%z", True),
            ("%Y-%m-%dT%H:%M:%S%z", True),
            ("%d/%b/%Y:%H:%M:%S %z", False),
            ("%d/%b/%Y:%H:%M:%S", False),
            ("%b %d %H:%M:%S", False),
            ("%Y/%m/%d %H:%M:%S", False),
            ("%m-%d-%Y %H:%M:%S", False),
        ]
        
        ts_str_normalized = ts_str
        if ts_str.endswith("Z"):
            ts_str_normalized = ts_str[:-1] + "+00:00"
        
        for fmt, has_tz in formats:
            try:
                if has_tz:
                    return datetime.strptime(ts_str_normalized, fmt)
                else:
                    if "%b" in fmt:
                        dt = datetime.strptime(ts_str, fmt)
                        return dt.replace(year=year)
                    return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        
        try:
            return datetime.fromisoformat(ts_str_normalized.replace("Z", "+00:00"))
        except ValueError:
            pass
        
        return None
