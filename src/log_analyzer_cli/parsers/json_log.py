"""JSON log format parser."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Optional

from log_analyzer_cli.parsers.base import LogParser, ParsedEntry
from log_analyzer_cli.utils import detect_log_level


class JSONLogParser(LogParser):
    """Parser for JSON structured logs.
    
    Supports common JSON log formats including:
    - Logfmt-style JSON
    - Cloud logging formats (GCP, AWS, Azure)
    - Application JSON logs with various field names
    """
    
    name = "json"
    description = "JSON structured log parser"
    
    TIMESTAMP_FIELDS = [
        "timestamp", "time", "ts", "@timestamp", "datetime", 
        "date", "created_at", "created", "logged_at"
    ]
    
    LEVEL_FIELDS = [
        "level", "severity", "loglevel", "log_level", "lvl", 
        "priority", "importance"
    ]
    
    MESSAGE_FIELDS = [
        "message", "msg", "text", "log", "body", "content"
    ]
    
    def can_parse(self, line: str) -> bool:
        """Check if line is valid JSON."""
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            return False
        try:
            json.loads(line)
            return True
        except json.JSONDecodeError:
            return False
    
    def parse(self, line: str) -> Optional[ParsedEntry]:
        """Parse a JSON log line."""
        try:
            data = json.loads(line.strip())
        except json.JSONDecodeError:
            return None
        
        timestamp = self._extract_timestamp(data)
        level = self._extract_level(data)
        message = self._extract_message(data)
        
        metadata = {k: v for k, v in data.items() 
                   if k not in self.TIMESTAMP_FIELDS + self.LEVEL_FIELDS + self.MESSAGE_FIELDS}
        
        return ParsedEntry(
            raw=line,
            timestamp=timestamp,
            level=level,
            message=message,
            metadata=metadata,
        )
    
    def _extract_timestamp(self, data: dict) -> Optional[datetime]:
        """Extract timestamp from JSON data."""
        for field in self.TIMESTAMP_FIELDS:
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    if value >= 1e12:
                        return datetime.fromtimestamp(value / 1000)
                    return datetime.fromtimestamp(value)
                if isinstance(value, str):
                    return self._parse_timestamp_string(value)
        return None
    
    def _parse_timestamp_string(self, ts_str: str) -> Optional[datetime]:
        """Parse timestamp string from JSON."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S",
        ]
        
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        
        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        
        ts_str_clean = re.sub(r'\.\d+Z$', '+00:00', ts_str)
        try:
            return datetime.fromisoformat(ts_str_clean.replace("Z", "+00:00"))
        except ValueError:
            pass
        
        return None
    
    def _extract_level(self, data: dict) -> str:
        """Extract log level from JSON data."""
        for field in self.LEVEL_FIELDS:
            if field in data:
                level = str(data[field]).upper()
                if level in ("ERR", "ERRO"):
                    return "ERROR"
                if level in ("WARN", "WRN"):
                    return "WARNING"
                if level in ("DBG", "DEBUG"):
                    return "DEBUG"
                if level in ("TRACE", "TRC"):
                    return "TRACE"
                if level in ("CRIT", "CRITICAL", "FATAL"):
                    return "CRITICAL"
                return level
        return "UNKNOWN"
    
    def _extract_message(self, data: dict) -> str:
        """Extract message from JSON data."""
        for field in self.MESSAGE_FIELDS:
            if field in data:
                return str(data[field])
        return str(data)
