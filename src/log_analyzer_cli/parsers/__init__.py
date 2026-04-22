"""Log parsers for different formats."""

from log_analyzer_cli.parsers.apache import ApacheParser
from log_analyzer_cli.parsers.base import LogParser, ParsedEntry
from log_analyzer_cli.parsers.generic import GenericParser
from log_analyzer_cli.parsers.json_log import JSONLogParser
from log_analyzer_cli.parsers.syslog import SyslogParser

__all__ = [
    "LogParser",
    "ParsedEntry",
    "SyslogParser",
    "JSONLogParser",
    "ApacheParser",
    "GenericParser",
]


def get_all_parsers() -> list[type[LogParser]]:
    """Get all available parser classes."""
    return [
        JSONLogParser,
        SyslogParser,
        ApacheParser,
        GenericParser,
    ]


def auto_detect_parser(line: str) -> type[LogParser] | None:
    """Auto-detect the best parser for a log line.
    
    Args:
        line: A sample line from the log file.
        
    Returns:
        Parser class that can handle the line, or None.
    """
    for parser_class in get_all_parsers():
        parser = parser_class()
        if parser.can_parse(line):
            return parser_class
    return None


def get_parser_for_format(format_name: str) -> type[LogParser] | None:
    """Get a parser class by name.
    
    Args:
        format_name: Name of the format (e.g., 'json', 'syslog', 'apache', 'generic').
        
    Returns:
        Parser class or None if not found.
    """
    format_map = {
        "json": JSONLogParser,
        "syslog": SyslogParser,
        "apache": ApacheParser,
        "generic": GenericParser,
    }
    parser_cls = format_map.get(format_name.lower())
    if parser_cls is None:
        raise ValueError(f"Unknown log format: '{format_name}'. Choose from: {', '.join(format_map.keys())}")
    return parser_cls