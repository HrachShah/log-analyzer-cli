"""Tests for CLI."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from click.testing import CliRunner

from log_analyzer_cli.cli import _parse_file, main
from log_analyzer_cli.parsers import GenericParser


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
    
    def test_parse_file_handles_aware_timestamp_with_naive_filter(self, tmp_path):
        path = tmp_path / "aware.log"
        path.write_text("2025-03-20T10:15:32+01:00 INFO Application started\n")

        entries = _parse_file(
            GenericParser(),
            path,
            start_time=datetime(2025, 3, 20, 9, 15, 32),
        )

        assert len(entries) == 1

    def test_parse_file_handles_naive_timestamp_with_aware_filter(self, tmp_path):
        path = tmp_path / "naive.log"
        path.write_text("2025-03-20 10:15:32 INFO Application started\n")

        entries = _parse_file(
            GenericParser(),
            path,
            start_time=datetime(2025, 3, 20, 10, 15, 32, tzinfo=timezone.utc),
        )

        assert len(entries) == 1

    def test_analyze_auto_format_detection(self, runner, json_file):
        result = runner.invoke(main, ["analyze", str(json_file), "--format", "auto"])
        assert result.exit_code == 0
    
    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "formats" in result.output
