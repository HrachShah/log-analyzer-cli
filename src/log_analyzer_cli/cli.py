"""CLI entry point for log-analyzer-cli."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from log_analyzer_cli import __version__
from log_analyzer_cli.analyzer import LogAnalyzer, analyze_log_entries
from log_analyzer_cli.formatters import format_output
from log_analyzer_cli.parsers import (
    GenericParser,
    JSONLogParser,
    SyslogParser,
    ApacheParser,
    get_all_parsers,
    get_parser_for_format,
)
from log_analyzer_cli.utils import read_log_file


@click.group()
@click.version_option(version=__version__, prog_name="log-analyzer-cli")
def main() -> None:
    """Log Analyzer CLI - Analyze log files and summarize errors, warnings, and metrics."""
    pass


@main.command()
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--format",
    "-f",
    "log_format",
    type=click.Choice(["auto", "json", "syslog", "apache", "generic"]),
    default="auto",
    help="Log format (auto-detect by default)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Include detailed output",
)
@click.option(
    "--no-group",
    is_flag=True,
    help="Disable error grouping",
)
@click.option(
    "--levels",
    "-l",
    help="Comma-separated list of log levels to include (ERROR,WARNING,INFO,DEBUG,CRITICAL)",
)
@click.option(
    "--pattern",
    "-p",
    help="Regex pattern to filter log lines",
)
@click.option(
    "--start-time",
    help="Filter entries after this timestamp (YYYY-MM-DD HH:MM:SS)",
)
@click.option(
    "--end-time",
    help="Filter entries before this timestamp (YYYY-MM-DD HH:MM:SS)",
)
def analyze(
    file: Path,
    log_format: str,
    output: str,
    verbose: bool,
    no_group: bool,
    levels: Optional[str],
    pattern: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
) -> None:
    """Analyze a log file and summarize errors, warnings, and metrics."""
    try:
        level_filter = None
        if levels:
            level_filter = [l.strip().upper() for l in levels.split(",")]
        
        from datetime import datetime
        
        start_dt = None
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                click.echo(f"Error: Invalid start-time format. Use YYYY-MM-DD HH:MM:SS", err=True)
                sys.exit(1)
        
        end_dt = None
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                click.echo(f"Error: Invalid end-time format. Use YYYY-MM-DD HH:MM:SS", err=True)
                sys.exit(1)
        
        parser = _get_parser(log_format, file)
        
        if not parser:
            click.echo("Error: Could not determine log format", err=True)
            sys.exit(1)
        
        click.echo(f"Using parser: {parser.name}")
        
        total_lines_out = [0]
        parse_errors_out = [0]
        entries = _parse_file(parser, file, level_filter, pattern, start_dt, end_dt, total_lines_out, parse_errors_out)
        
        if not entries:
            click.echo("No log entries found matching criteria", err=True)
            sys.exit(0)
        
        result = analyze_log_entries(entries, group_errors=not no_group)
        result.total_lines = total_lines_out[0]
        result.parse_errors = parse_errors_out[0]
        
        output_str = format_output(result, output, verbose)
        
        click.echo(output_str)
        
    except (ValueError, TypeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("formats")
def list_formats() -> None:
    """List supported log formats."""
    parsers = get_all_parsers()
    
    click.echo("Supported log formats:")
    click.echo("")
    
    for parser_class in parsers:
        parser = parser_class()
        click.echo(f"  {parser.name:10} - {parser.description}")


def _get_parser(format_name: str, file_path: Path, total_lines_out: Optional[list[int]] = None, parse_errors_out: Optional[list[int]] = None):
    """Get appropriate parser for the log file."""
    if format_name != "auto":
        return get_parser_for_format(format_name)()
    
    sample_lines = []
    total_lines = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                total_lines += 1
                line = line.strip()
                if line:
                    sample_lines.append(line)
                if total_lines >= 10:
                    break
    except OSError as e:
        click.echo(f"Warning: Could not read file: {e}", err=True)
        return None
    
    if total_lines_out is not None:
        total_lines_out[0] = total_lines
    
    if not sample_lines:
        return None
    
    for parser_class in get_all_parsers():
        parser = parser_class()
        for line in sample_lines[:5]:
            if parser.can_parse(line):
                return parser
    
    return GenericParser()


def _parse_file(
    parser,
    file_path: Path,
    include_levels: Optional[list[str]] = None,
    search_pattern: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    total_lines_out: Optional[list[int]] = None,
    parse_errors_out: Optional[list[int]] = None,
):
    """Parse log file with optional filtering."""
    entries = []
    parse_errors = 0
    
    from log_analyzer_cli.parsers import ParsedEntry
    from log_analyzer_cli.utils import detect_log_level, parse_timestamp
    import re
    
    compiled_pattern = re.compile(search_pattern) if search_pattern else None
    
    for line in read_log_file(file_path):
        line = line.rstrip("\n\r")
        if not line:
            continue
        
        if include_levels:
            level = detect_log_level(line)
            if level not in include_levels:
                continue
        
        if compiled_pattern and not compiled_pattern.search(line):
            continue
        
        timestamp = parse_timestamp(line)
        if start_time and timestamp and timestamp < start_time:
            continue
        if end_time and timestamp and timestamp > end_time:
            continue
        
        parsed = parser.parse(line)
        if parsed:
            entries.append(parsed)
        else:
            parse_errors += 1
    
    if total_lines_out is not None:
        total_lines_out[0] = len(entries) + parse_errors
    if parse_errors_out is not None:
        parse_errors_out[0] = parse_errors
    
    return entries


if __name__ == "__main__":
    main()
