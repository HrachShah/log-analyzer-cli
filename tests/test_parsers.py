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

    def test_parse_json_line_drops_only_timestamp_on_out_of_range_value(self):
        # An out-of-range numeric timestamp (year > 9999) used to raise
        # ValueError out of datetime.fromtimestamp and escape parse() entirely,
        # dropping the whole JSON log line and surfacing a traceback to the
        # CLI. The contract is that parse() returns None only when the JSON
        # itself is unparseable; for a valid JSON line with a busted numeric
        # timestamp, the entry should come back with timestamp=None.
        parser = JSONLogParser()

        # 1e15 seconds from epoch is year 33658, which is out of the
        # datetime range.
        line = '{"timestamp": 1e15, "level": "ERROR", "message": "huge ts"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is None
        assert entry.level == "ERROR"
        assert entry.message == "huge ts"

        # Negative timestamps far from the epoch are also out of range
        # (year -31686769).
        line = '{"timestamp": -1e15, "level": "INFO", "message": "old"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is None
        assert entry.level == "INFO"
        assert entry.message == "old"

        # 1e308 is larger than the platform time_t can represent and
        # raises OverflowError on the underlying fromtimestamp call.
        line = '{"timestamp": 1e308, "level": "WARN", "message": "overflow"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is None
        assert entry.level == "WARNING"
        assert entry.message == "overflow"

    def test_parse_json_line_keeps_valid_timestamp(self):
        # Sanity: the try/except around _extract_timestamp must not break
        # the normal path for a valid numeric timestamp.
        parser = JSONLogParser()
        line = '{"timestamp": 1700000000, "level": "INFO", "message": "ok"}'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2023
        assert entry.level == "INFO"


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


class TestApacheCombinedPatternExtraction:
    """Tests that the COMBINED_PATTERN regex actually matches a real combined log
    and properly extracts referer and user_agent fields.
    """

    def test_combined_pattern_extracts_referer(self):
        parser = ApacheParser()
        line = '192.168.1.10 - - [20/Mar/2025:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 2326 "https://example.com/" "Mozilla/5.0"'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.metadata.get("referer") == "https://example.com/"
        assert entry.metadata.get("user_agent") == "Mozilla/5.0"

    def test_combined_pattern_matches_with_dash_user(self):
        parser = ApacheParser()
        line = '10.0.0.1 - frank [20/Mar/2025:10:15:32 +0000] "GET /api HTTP/1.1" 200 100 "-" "curl/7.0"'
        entry = parser.parse(line)
        assert entry is not None
        assert entry.metadata["user"] == "frank"
        assert entry.metadata["referer"] == "-"
        assert entry.metadata["user_agent"] == "curl/7.0"
