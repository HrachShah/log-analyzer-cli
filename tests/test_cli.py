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

    def test_analyze_time_filter_naive_boundary_aware_log(self, runner, tmp_path):
        # JSON log lines carry Z-suffixed (tz-aware) timestamps; user-supplied
        # --start-time is parsed as a naive "YYYY-MM-DD HH:MM:SS" string. Before
        # the fix, the comparison crashed with
        # "can't compare offset-naive and offset-aware datetimes". The fix
        # attaches UTC to the parsed boundary and aligns the parsed timestamp
        # through _align_to_utc so all four combinations compare cleanly.
        from click.testing import CliRunner
        from log_analyzer_cli.cli import main as cli_main
        runner2 = CliRunner()
        log = tmp_path / "aware.log"
        log.write_text(
            '{"timestamp": "2026-04-20T10:30:00Z", "level": "INFO", "message": "match me"}\n'
            '{"timestamp": "2025-01-01T00:00:00Z", "level": "INFO", "message": "too old"}\n'
        )
        result = runner2.invoke(
            cli_main,
            ["analyze", str(log), "-f", "json", "--start-time", "2026-01-01 00:00:00"],
        )
        assert result.exit_code == 0
        assert "Total Lines" in result.output
        assert "Parsed Entries" in result.output

    def test_analyze_time_filter_mixed_naive_and_aware_log(self, runner, tmp_path):
        # Same boundary/parsed mismatch, but the log itself contains a mix of
        # naive "YYYY-MM-DD HH:MM:SS" syslog lines and tz-aware ISO lines.
        # Before the fix, the first cross-naive/aware comparison raised TypeError.
        from click.testing import CliRunner
        from log_analyzer_cli.cli import main as cli_main
        runner2 = CliRunner()
        log = tmp_path / "mixed.log"
        log.write_text(
            "2026-04-20 10:30:00 system kernel: match me\n"
            "2026-04-20T10:30:05Z INFO also match\n"
            "2025-01-01 00:00:00 system kernel: too old\n"
        )
        result = runner2.invoke(
            cli_main,
            ["analyze", str(log), "--start-time", "2026-01-01 00:00:00"],
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
