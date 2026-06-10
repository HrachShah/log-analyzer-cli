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
    
    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "formats" in result.output


class TestParseErrors:
    """Tests for the parse_errors / total_lines accounting fix."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def _make_log(self, lines):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
        for line in lines:
            f.write(line + "\n")
        f.close()
        return f.name

    def test_total_lines_counts_all_non_empty_input(self, runner):
        path = self._make_log([
            '{"timestamp": "2025-03-20T10:15:32", "level": "INFO", "message": "ok1"}',
            "this is not valid json",
            '{"timestamp": "2025-03-20T10:16:00", "level": "ERROR", "message": "ok2"}',
            "neither is this",
            '{"timestamp": "2025-03-20T10:17:00", "level": "INFO", "message": "ok3"}',
        ])
        import os
        try:
            result = runner.invoke(main, ["analyze", path, "-f", "json", "-o", "json"])
            assert result.exit_code == 0
            import json
            data = json.loads(result.output.split("\n", 1)[1])
            assert data["summary"]["total_lines"] == 5
            assert data["summary"]["parsed_entries"] == 3
            assert data["summary"]["parse_errors"] == 2
        finally:
            os.unlink(path)

    def test_skipped_filtered_warns(self, runner):
        path = self._make_log([
            '{"timestamp": "2025-03-20T10:15:32", "level": "INFO", "message": "kept"}',
            '{"timestamp": "2025-03-20T10:16:00", "level": "DEBUG", "message": "filtered"}',
            '{"timestamp": "2025-03-20T10:17:00", "level": "INFO", "message": "kept2"}',
        ])
        import os
        try:
            result = runner.invoke(
                main, ["analyze", path, "-f", "json", "-o", "json", "-l", "INFO"]
            )
            assert result.exit_code == 0
            import json
            data = json.loads(result.output.split("\n", 1)[1])
            # 3 input lines, 1 was filtered by the level filter, 2 kept
            assert data["summary"]["total_lines"] == 2
            assert data["summary"]["parsed_entries"] == 2
            assert "warnings" in data
            assert any("Skipped" in w for w in data["warnings"])
        finally:
            os.unlink(path)

    def test_empty_file_no_entries_message(self, runner):
        path = self._make_log([])
        import os
        try:
            result = runner.invoke(main, ["analyze", path, "-f", "json", "-o", "json"])
            # No entries means CLI prints the 'No log entries found' message
            # and exits 0. We just need to make sure it does not crash and
            # total_lines is not garbage.
            assert result.exit_code == 0
            assert "No log entries" in result.output
        finally:
            os.unlink(path)