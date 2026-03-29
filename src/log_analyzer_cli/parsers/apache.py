"""Apache/Nginx log format parser."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from log_analyzer_cli.parsers.base import LogParser, ParsedEntry


class ApacheParser(LogParser):
    """Parser for Apache/Nginx access logs.
    
    Supports:
    - Combined Log Format
    - Common Log Format
    - Custom formats
    """
    
    name = "apache"
    description = "Apache/Nginx access log parser"
    
    COMBINED_PATTERN = re.compile(
        r'^(?P<host>\S+)\s+'
        r'(?P<ident>\S+)\s+'
        r'(?P<user>\s+)'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<request>[^"]+)"\s+'
        r'(?P<status>\d{3})\s+'
        r'(?P<size>\S+)'
        r'(?:\s+"(?P<referer>[^"]+)"\s+"(?P<user_agent>[^"]+)")?'
        r'.*$'
    )
    
    COMMON_PATTERN = re.compile(
        r'^(?P<host>\S+)\s+'
        r'(?P<ident>\S+)\s+'
        r'(?P<user>\S+)\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<request>[^"]+)"\s+'
        r'(?P<status>\d{3})\s+'
        r'(?P<size>\S+)'
        r'.*$'
    )
    
    def can_parse(self, line: str) -> bool:
        """Check if line looks like Apache/Nginx access log."""
        line = line.strip()
        if not line:
            return False
        
        if self.COMBINED_PATTERN.match(line) or self.COMMON_PATTERN.match(line):
            return True
        
        return False
    
    def parse(self, line: str) -> Optional[ParsedEntry]:
        """Parse an Apache/Nginx log line."""
        match = self.COMBINED_PATTERN.match(line)
        if not match:
            match = self.COMMON_PATTERN.match(line)
        
        if not match:
            return None
        
        groups = match.groupdict()
        
        timestamp = self._parse_timestamp(groups.get("timestamp", ""))
        
        status = groups.get("status", "")
        if status:
            status_int = int(status)
            if status_int >= 500:
                level = "ERROR"
            elif status_int >= 400:
                level = "WARNING"
            else:
                level = "INFO"
        else:
            level = "UNKNOWN"
        
        metadata = {
            "host": groups.get("host", ""),
            "user": groups.get("user", ""),
            "request": groups.get("request", ""),
            "status": status,
            "size": groups.get("size", ""),
        }
        
        if groups.get("referer"):
            metadata["referer"] = groups["referer"]
        if groups.get("user_agent"):
            metadata["user_agent"] = groups["user_agent"]
        
        message = f"{groups.get('request', '')} - Status: {status}"
        
        return ParsedEntry(
            raw=line,
            timestamp=timestamp,
            level=level,
            message=message,
            source=groups.get("host"),
            metadata=metadata,
        )
    
    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parse Apache timestamp format."""
        if not ts_str:
            return None
        
        try:
            return datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            pass
        
        try:
            ts_str_naive = ts_str.split()[0]
            return datetime.strptime(ts_str_naive, "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            pass
        
        return None
