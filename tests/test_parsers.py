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


class TestJSONNumericTimestampUnits:
    """Tests for JSONLogParser with numeric timestamp units."""
    
    def test_parse_json_with_microsecond_timestamp(self):
        # Go's time.Now().UnixMicro() emits a 16-digit value (~1.6e15).
        # The old code divided by 1000 only once, leaving a value still
        # far above the second-resolution epoch and crashing with
        # "year ... is out of range".
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2022
        assert entry.timestamp.month == 3
        assert entry.timestamp.day == 20
        assert entry.timestamp.hour == 12
        assert entry.timestamp.minute == 53
        assert entry.timestamp.second == 20

    def test_parse_json_with_nanosecond_timestamp(self):
        # Go's time.Now().UnixNano() emits a 19-digit value (~1.6e18).
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800000000000, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2022
        assert entry.timestamp.month == 3
        assert entry.timestamp.day == 20
        assert entry.timestamp.hour == 12
        assert entry.timestamp.minute == 53
        assert entry.timestamp.second == 20

    def test_parse_json_with_seconds_timestamp(self):
        # Plain unix seconds - the smallest numeric unit.
        parser = JSONLogParser()
        line = '{"timestamp": 1647780800, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2022
        assert entry.timestamp.month == 3
        assert entry.timestamp.day == 20

    def test_parse_json_with_out_of_range_timestamp_returns_none(self):
        # A value so large that no unit rescaling maps to a real datetime
        # must return None rather than leak ValueError.
        parser = JSONLogParser()
        line = '{"timestamp": 1e30, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is None

    def test_parse_json_with_nan_numeric_timestamp_returns_none(self):
        # float('nan') is technically a number; the old code would feed it
        # straight into datetime.fromtimestamp and raise ValueError.
        parser = JSONLogParser()
        line = '{"timestamp": NaN, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is None

    def test_parse_json_with_null_timestamp_returns_none(self):
        parser = JSONLogParser()
        line = '{"timestamp": null, "level": "INFO", "message": "x"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is None