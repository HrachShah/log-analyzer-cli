"""Tests for log parsers."""

from __future__ import annotations

import pytest

from log_analyzer_cli.parsers import (
    GenericParser,
    JSONLogParser,
    SyslogParser,
    ApacheParser,
    get_parser_for_format,
)


class TestSyslogParser:
    """Tests for SyslogParser."""
    
    def test_can_parse_syslog_format(self):
        parser = SyslogParser()
        line = "2025-03-20 10:15:32 systemkernel: System boot completed"
        assert parser.can_parse(line) is True
    
    def test_can_parse_syslog_with_pid(self):
        parser = SyslogParser()
        line = "2025-03-20 10:16:01 CRON[1234]: Starting daily tasks"
        assert parser.can_parse(line) is True
    
    def test_can_parse_rfc3164_format(self):
        parser = SyslogParser()
        line = "Mar 20 10:15:32 hostname process[123]: Message"
        assert parser.can_parse(line) is True
    
    def test_parse_syslog_line(self):
        parser = SyslogParser()
        line = "2025-03-20 10:15:32 systemkernel: System boot completed"
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.message == "System boot completed"
        assert entry.source == "systemkernel"
    
    def test_parse_syslog_with_level(self):
        parser = SyslogParser()
        line = "2025-03-20 10:25:42 apache2[5678]: ERROR: Database connection failed"
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.level == "ERROR"
        assert "Database connection failed" in entry.message


class TestJSONLogParser:
    """Tests for JSONLogParser."""
    
    def test_can_parse_json(self):
        parser = JSONLogParser()
        line = '{"timestamp": "2025-03-20T10:15:32.123Z", "level": "INFO", "message": "Started"}'
        assert parser.can_parse(line) is True
    
    def test_cannot_parse_non_json(self):
        parser = JSONLogParser()
        line = "2025-03-20 10:15:32 systemkernel: Message"
        assert parser.can_parse(line) is False
    
    def test_parse_json_line(self):
        parser = JSONLogParser()
        line = '{"timestamp": "2025-03-20T10:15:32.123Z", "level": "INFO", "message": "Started"}'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.level == "INFO"
        assert entry.message == "Started"
    
    def test_parse_json_with_numeric_timestamp(self):
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800000, "level": "ERROR", "message": "Failed"}'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.level == "ERROR"
    
    def test_parse_json_various_level_names(self):
        parser = JSONLogParser()
        
        for level_field in ["level", "severity", "loglevel"]:
            line = f'{{"{level_field}": "error", "message": "Test"}}'
            entry = parser.parse(line)
            assert entry is not None
            assert entry.level == "ERROR"


class TestApacheParser:
    """Tests for ApacheParser."""
    
    def test_can_parse_combined_format(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0"'
        assert parser.can_parse(line) is True
    
    def test_can_parse_common_format(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 2326'
        assert parser.can_parse(line) is True
    
    def test_parse_apache_combined(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0"'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.level == "INFO"
        assert entry.metadata["status"] == "200"
    
    def test_parse_apache_error_status(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 500 2326'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.level == "ERROR"
    
    def test_parse_apache_warning_status(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 404 2326'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.level == "WARNING"


class TestGenericParser:
    """Tests for GenericParser."""
    
    def test_can_parse_generic_timestamp(self):
        parser = GenericParser()
        line = "2025-03-20 10:15:32 INFO Application started"
        assert parser.can_parse(line) is True
    
    def test_can_parse_iso_timestamp(self):
        parser = GenericParser()
        line = "2025-03-20T10:15:32.123Z INFO Application started"
        assert parser.can_parse(line) is True
    
    def test_parse_generic_line(self):
        parser = GenericParser()
        line = "2025-03-20 10:15:32 INFO Application started"
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.level == "INFO"
        assert "Application started" in entry.message


class TestParserUtils:
    """Tests for parser utility functions."""
    
    def test_get_parser_for_format(self):
        parser_class = get_parser_for_format("json")
        assert parser_class == JSONLogParser
        
        parser_class = get_parser_for_format("syslog")
        assert parser_class == SyslogParser
        
        parser_class = get_parser_for_format("apache")
        assert parser_class == ApacheParser
        
        parser_class = get_parser_for_format("generic")
        assert parser_class == GenericParser
    
    def test_get_parser_for_format_case_insensitive(self):
        parser_class = get_parser_for_format("JSON")
        assert parser_class == JSONLogParser
    
    def test_get_parser_for_format_invalid(self):
        parser_class = get_parser_for_format("invalid_format")
        assert parser_class is None


class TestJSONTimestampWidth:
    """Tests for JSON timestamp width detection fix."""
    
    def test_seconds(self):
        parser = JSONLogParser()
        line = '{"timestamp": "2025-03-20T10:15:32Z", "level": "INFO", "message": "Started"}'
        assert parser.can_parse(line) is True
    
    def test_milliseconds(self):
        parser = JSONLogParser()
        line = '{"timestamp": "2025-03-20T10:15:32.123Z", "level": "INFO", "message": "Started"}'
        assert parser.can_parse(line) is True
    
    def test_microseconds(self):
        parser = JSONLogParser()
        line = '{"timestamp": "2025-03-20T10:15:32.123456Z", "level": "INFO", "message": "Started"}'
        assert parser.can_parse(line) is True
    
    def test_seconds_numeric(self):
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800, "level": "ERROR", "message": "Failed"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.level == "ERROR"
    
    def test_milliseconds_numeric(self):
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800123, "level": "ERROR", "message": "Failed"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.level == "ERROR"

# ===================================================================
# Width-based numeric timestamp detection
# ===================================================================


class TestJSONNumericTimestampWidth:
    """Width-based detection of seconds / ms / us / ns numeric timestamps.

    The parser used to treat any numeric timestamp > 1e12 as milliseconds
    and anything else as seconds. That collapsed microsecond and
    nanosecond timestamps together with millisecond ones, raising
    ``ValueError: year 55840 is out of range`` on microsecond inputs and
    silently overflowing on nanosecond inputs.
    """

    def test_seconds_is_treated_as_seconds(self):
        # 1_700_000_000 = 2023-11-14 in seconds.
        parser = JSONLogParser()
        line = '{"timestamp": 1700000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2023
        assert entry.timestamp.month == 11
        assert entry.timestamp.day == 14

    def test_milliseconds_is_treated_as_milliseconds(self):
        # 1_700_000_000_000 = 2023-11-14 in milliseconds.
        parser = JSONLogParser()
        line = '{"timestamp": 1700000000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2023
        assert entry.timestamp.month == 11
        assert entry.timestamp.day == 14

    def test_microseconds_is_treated_as_microseconds(self):
        # 1_700_000_000_000_000 = 2023-11-14 in microseconds.
        parser = JSONLogParser()
        line = '{"timestamp": 1700000000000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2023
        assert entry.timestamp.month == 11
        assert entry.timestamp.day == 14

    def test_nanoseconds_is_treated_as_nanoseconds(self):
        # 1_700_000_000_000_000_000 = 2023-11-14 in nanoseconds.
        parser = JSONLogParser()
        line = '{"timestamp": 1700000000000000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2023
        assert entry.timestamp.month == 11
        assert entry.timestamp.day == 14

    def test_zero_timestamp_yields_none(self):
        parser = JSONLogParser()
        line = '{"timestamp": 0, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is None

    def test_negative_timestamp_yields_none(self):
        parser = JSONLogParser()
        line = '{"timestamp": -1, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is None
