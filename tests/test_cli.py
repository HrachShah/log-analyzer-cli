"""Tests for CLI."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from log_analyzer_cli.cli import main


class TestCLI:
    """Tests for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "log-analyzer-cli" in result.output.lower() or "1.0.0" in result.output
        assert "1.0.0" in result.output
    
    def test_list_formats(self, runner):
        result = runner.invoke(main, ["formats"])
        assert result.exit_code == 0
        assert "json" in result.output
        assert "syslog" in result.output
        assert "apache" in result.output
        assert "generic" in result.output
    
    def test_analyze_missing_file(self, runner):
        result = runner.invoke(main, ["analyze", "nonexistent.log"])
        assert result.exit_code != 0
    
    def test_analyze_syslog_file(self, runner, syslog_file):
        result = runner.invoke(main, ["analyze", str(syslog_file)])
        assert result.exit_code == 0
        assert "LOG ANALYSIS REPORT" in result.output
        assert "Total Lines" in result.output
    
    def test_analyze_json_file(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-f", "json"])
        assert result.exit_code == 0
        assert "LOG ANALYSIS REPORT" in result.output
    
    def test_analyze_apache_file(self, runner, apache_file):
        result = runner.invoke(main, ["analyze", str(apache_file), "-f", "apache"])
        assert result.exit_code == 0
        assert "LOG ANALYSIS REPORT" in result.output
    
    def test_analyze_output_json(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-f", "json", "-o", "json"])
        assert result.exit_code == 0
        assert "{" in result.output
        assert "summary" in result.output
    
    def test_analyze_output_table(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-o", "table"])
        assert result.exit_code == 0
        assert "+" in result.output or "|" in result.output
    
    def test_analyze_verbose(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-v"])
        assert result.exit_code == 0
        assert "Sample messages" in result.output
    
    def test_analyze_no_group(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "--no-group"])
        assert result.exit_code == 0
    
    def test_analyze_level_filter(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-l", "ERROR,WARNING"])
        assert result.exit_code == 0
    
    def test_analyze_pattern_filter(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "-p", "database"])
        assert result.exit_code == 0
    
    def test_analyze_time_filter(self, runner, json_file):
        result = runner.invoke(
            main,
            ["analyze", str(json_file), "--start-time", "2025-03-20 10:00:00"]
        )
        assert result.exit_code == 0
    
    def test_analyze_auto_format_detection(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "--format", "auto"])
        assert result.exit_code == 0

    def test_analyze_time_filter_naive_start_with_aware_log(self, runner, tmp_path):
        """Naive --start-time must compare against TZ-aware log timestamps without raising."""
        import json as json_mod
        log = tmp_path / "tz-aware.log"
        log.write_text(
            json_mod.dumps({
                "timestamp": "2025-03-20T10:15:32.123Z",
                "level": "INFO",
                "message": "Started",
            }) + "\n" +
            json_mod.dumps({
                "timestamp": "2025-03-20T10:17:00.000Z",
                "level": "ERROR",
                "message": "Failed",
            }) + "\n"
        )
        result = runner.invoke(
            main,
            ["analyze", str(log), "-f", "json", "-o", "json",
             "--start-time", "2025-03-20 10:16:00"],
        )
        assert result.exit_code == 0, result.output
        assert '"parsed_entries": 1' in result.output
        assert "ERROR" in result.output
        assert "Started" not in result.output

    def test_analyze_level_filter_uses_parser_level_not_raw_text(self, runner, tmp_path):
        """--levels filters by the parser's level, not the raw-line keyword scan."""
        log = tmp_path / "apache.log"
        log.write_text(
            '127.0.0.1 - - [20/Mar/2025:10:15:32 +0000] '
            '"GET / HTTP/1.1" 200 1234 "-" "Mozilla/ERROR/5.0"\n'
            '127.0.0.1 - - [20/Mar/2025:10:15:33 +0000] '
            '"GET /api HTTP/1.1" 500 5678 "-" "curl/8.0"\n'
        )
        result = runner.invoke(
            main,
            ["analyze", str(log), "-f", "apache", "-o", "json", "-l", "ERROR"],
        )
        assert result.exit_code == 0, result.output
        assert '"parsed_entries": 1' in result.output
        assert "ERROR" in result.output
        result = runner.invoke(
            main,
            ["analyze", str(log), "-f", "apache", "-o", "json", "-l", "INFO"],
        )
        assert result.exit_code == 0, result.output
        assert '"parsed_entries": 1' in result.output
        assert "INFO" in result.output

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "formats" in result.output