"""Output formatters for log-analyzer-cli."""

from log_analyzer_cli.analyzer import AnalysisResult
from log_analyzer_cli.formatters.json import format_json
from log_analyzer_cli.formatters.table import format_table
from log_analyzer_cli.formatters.text import format_text

__all__ = [
    "format_text",
    "format_json",
    "format_table",
]


def format_output(result: AnalysisResult, format_type: str = "text", verbose: bool = False) -> str:
    """Format analysis result in the specified format.
    
    Args:
        result: Analysis result to format.
        format_type: Output format ('text', 'json', 'table').
        verbose: Include more detailed output (only for text).
        
    Returns:
        Formatted output string.
    """
    format_type = format_type.lower()
    
    if format_type == "json":
        return format_json(result)
    elif format_type == "table":
        return format_table(result)
    else:
        return format_text(result, verbose)
