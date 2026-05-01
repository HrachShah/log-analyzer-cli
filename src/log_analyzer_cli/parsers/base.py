"""Base parser class for log-analyzer-cli."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ParsedEntry:
    """A parsed log entry."""
    raw: str
    timestamp: Optional[datetime] = None
    level: str = "UNKNOWN"
    message: str = ""
    source: Optional[str] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LogParser(ABC):
    """Abstract base class for log parsers."""
    
    name: str = "base"
    description: str = "Base log parser"
    
    @abstractmethod
    def can_parse(self, line: str) -> bool:
        """Check if this parser can handle the given line.
        
        Args:
            line: A line from the log file.
            
        Returns:
            True if this parser can handle the line, False otherwise.
        """
        pass
    
    @abstractmethod
    def parse(self, line: str) -> Optional[ParsedEntry]:
        """Parse a log line.
        
        Args:
            line: A line from the log file.
            
        Returns:
            ParsedEntry or None if parsing failed.
        """
        pass
    
    def parse_file(self, file_path: str) -> list[ParsedEntry]:
        """Parse an entire log file.
        
        Args:
            file_path: Path to the log file.
            
        Returns:
            List of parsed entries.
        """
        from log_analyzer_cli.utils import read_log_file
        
        entries = []
        for line in read_log_file(file_path):
            stripped = line.rstrip("\n\r")
            if stripped and self.can_parse(stripped):
                entry = self.parse(stripped)
                if entry:
                    entries.append(entry)
        return entries
