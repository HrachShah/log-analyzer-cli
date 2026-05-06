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
    last_parse_errors: int = 0
    
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
            
        After this call, check `self.last_parse_errors` for the count of lines
        that could not be parsed (either can_parse returned False or parse
        raised an exception).
        """
        from log_analyzer_cli.utils import read_log_file
        
        entries = []
        self.last_parse_errors = 0
        for line in read_log_file(file_path):
            stripped = line.rstrip("\n\r")
            if stripped and self.can_parse(stripped):
                try:
                    entry = self.parse(stripped)
                except Exception:
                    entry = None
                if entry:
                    entries.append(entry)
                elif entry is None:
                    # parse() returned None explicitly — malformed line for this parser
                    self.last_parse_errors += 1
            else:
                self.last_parse_errors += 1
        return entries