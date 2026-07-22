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

    def test_parse_syslog_with_rfc3339_z_suffix(self):
        """RFC 3339 'Z' UTC suffix should be parsed, not silently dropped.

        A syslog line whose timestamp uses the ISO 8601 / RFC 3339 single-
        letter 'Z' UTC suffix (e.g. ``2025-03-20T10:15:32Z``) used to skip
        every ``strptime`` format because ``%z`` does not match 'Z', so
        ``_parse_timestamp`` returned ``None`` and the entry was stored
        with a missing timestamp. The fix normalises the trailing 'Z' to
        ``+00:00`` before ``strptime``.
        """
        parser = SyslogParser()
        line = "2025-03-20T10:15:32Z web01 app[1234]: something happened"
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.year == 2025
        assert entry.timestamp.month == 3
        assert entry.timestamp.day == 20
        assert entry.timestamp.hour == 10
        assert entry.timestamp.minute == 15
        assert entry.timestamp.second == 32
        assert entry.timestamp.utcoffset() is not None
        assert entry.message == "something happened"

    def test_parse_syslog_with_rfc3339_compact_offset(self):
        parser = SyslogParser()
        line = "2025-03-20T10:15:32+0000 web01 app: compact offset"
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.utcoffset().total_seconds() == 0
        assert entry.message == "compact offset"

    def test_parse_syslog_with_rfc3339_z_suffix_and_fractional_seconds(self):
        """The 'Z' suffix should also work with the fractional-seconds form."""
        parser = SyslogParser()
        line = "2025-03-20T10:15:32.500Z web01 app: fractional z"
        entry = parser.parse(line)

        assert entry is not None
        assert entry.timestamp is not None
        assert entry.timestamp.microsecond == 500000
        assert entry.message == "fractional z"


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
    
    def test_parse_json_array_returns_no_entry(self):
        parser = JSONLogParser()
        assert parser.parse('[{"message": "not a log object"}]') is None

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
        assert entry.timestamp is not None
        assert entry.timestamp.tzinfo is not None
        assert entry.timestamp.utcoffset().total_seconds() == 0

    def test_parse_json_various_level_names(self):
        parser = JSONLogParser()
        
        for level_field in ["level", "severity", "loglevel"]:
            line = f'{{"{level_field}": "error", "message": "Test"}}'
            entry = parser.parse(line)
            assert entry is not None
            assert entry.level == "ERROR"
    
    def test_parse_json_with_out_of_range_epoch_returns_entry_without_timestamp(self):
        """Far-future epoch (overflows datetime) should not crash the parser."""
        parser = JSONLogParser()
        # 253402300800 is 9999-01-01 UTC, which fromtimestamp rejects as
        # 'year 10000 is out of range'. The previous code let that
        # ValueError escape and the whole entry was dropped.
        line = '{"timestamp": 253402300800, "level": "INFO", "message": "future"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.message == "future"
        assert entry.timestamp is None

    def test_parse_json_with_negative_overflow_epoch_returns_entry_without_timestamp(self):
        """Far-past epoch (year overflow) should not crash the parser."""
        parser = JSONLogParser()
        # -1e15 seconds is well before year 1; fromtimestamp raises
        # 'year -1199 is out of range'. Same regression as the
        # far-future case.
        line = '{"timestamp": -1000000000000, "level": "ERROR", "message": "past"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.message == "past"
        assert entry.timestamp is None

    def test_parse_json_with_giant_float_epoch_returns_entry_without_timestamp(self):
        """Float epoch too large for platform time_t should not crash."""
        parser = JSONLogParser()
        # 1e30 seconds is 31.7 trillion years — overflows platform time_t
        # on 64-bit. The old code raised 'timestamp out of range for
        # platform time_t' and dropped the entry.
        line = '{"timestamp": 1.0e30, "level": "WARN", "message": "ancient"}'
        entry = parser.parse(line)

        assert entry is not None
        assert entry.message == "ancient"
        assert entry.timestamp is None

    def test_parse_json_with_missing_timestamp(self):
        parser = JSONLogParser()
        line = '{"level": "INFO", "message": "Test"}'
        entry = parser.parse(line)
        
        assert entry is not None
        assert entry.level == "INFO"
        assert entry.message == "Test"


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
