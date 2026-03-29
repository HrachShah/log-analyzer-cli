"""Syslog format parser."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from log_analyzer_cli.parsers.base import LogParser, ParsedEntry
from log_analyzer_cli.utils import detect_log_level


class SyslogParser(LogParser):
    """Parser for syslog format logs.
    
    Supports multiple syslog formats:
    - RFC 3164: <timestamp> <host> <process>: <message>
    - RFC 5424: <timestamp> <host> <process>[<pid>]: <message>
    - Common variants with different timestamp formats
    """
    
    name = "syslog"
    description = "Syslog format parser (RFC 3164/5424)"
    
    PATTERNS = [
        re.compile(
            r'^'
            r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
            r'\s+'
            r'(?P<host>\S+)'
            r'\s+'
            r'(?P<process>\S+?)'
            r'(?:\[(?P<pid>\d+)\])?'
            r':\s*'
            r'(?P<message>.*)'
            r'$'
        ),
        re.compile(
            r'^'
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)'
            r'\s+'
            r'(?P<host>\S+)'
            r'\s+'
            r'(?P<process>\S+?)'
            r'(?:\[(?P<pid>\d+)\])?'
            r':\s*'
            r'(?P<message>.*)'
            r'$'
        ),
        re.compile(
            r'^'
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
            r'\s+'
            r'(?P<host>\S+)'
            r'\s+'
            r'(?P<process>\S+?)'
            r'(?:\[(?P<pid>\d+)\])?'
            r':\s*'
            r'(?P<message>.*)'
            r'$'
        ),
        re.compile(
            r'^'
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
            r'\s+'
            r'(?P<host>\S+)'
            r':\s*'
            r'(?P<message>.*)'
            r'$'
        ),
    ]
    
    def can_parse(self, line: str) -> bool:
        """Check if line looks like syslog format."""
        for pattern in self.PATTERNS:
            if pattern.match(line):
                return True
        return False
    
    def parse(self, line: str) -> Optional[ParsedEntry]:
        """Parse a syslog line."""
        for pattern in self.PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groupdict()
                
                timestamp = self._parse_timestamp(groups.get("timestamp", ""))
                level = detect_log_level(line)  # Check full line for level
                
                metadata = {}
                if groups.get("host"):
                    metadata["host"] = groups["host"]
                if groups.get("process"):
                    metadata["process"] = groups["process"]
                    source = groups["process"]
                else:
                    # Use host as source when no process name
                    source = groups.get("host")
                if groups.get("pid"):
                    metadata["pid"] = groups["pid"]
                
                return ParsedEntry(
                    raw=line,
                    timestamp=timestamp,
                    level=level,
                    message=groups.get("message", "").strip(),
                    source=source,
                    metadata=metadata,
                )
        return None
    
    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parse syslog timestamp."""
        if not ts_str:
            return None
        
        year = datetime.now().year
        formats = [
            "%b %d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        
        for fmt in formats:
            try:
                if fmt == "%b %d %H:%M:%S":
                    dt = datetime.strptime(ts_str, fmt)
                    dt = dt.replace(year=year)
                    return dt
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        return None
