"""Table output formatter."""

from __future__ import annotations

from log_analyzer_cli.analyzer import AnalysisResult


def format_table(result: AnalysisResult) -> str:
    """Format analysis result as a table.
    
    Args:
        result: Analysis result to format.
        
    Returns:
        Formatted table string.
    """
    lines = []
    
    lines.append("+" + "-" * 58 + "+")
    lines.append("|" + " LOG ANALYSIS SUMMARY ".center(58) + "|")
    lines.append("+" + "-" * 58 + "+")
    
    lines.append(f"| {'Metric':<30} | {'Value':>25} |")
    lines.append("+" + "-" * 58 + "+")
    
    lines.append(f"| {'Total Lines':<30} | {result.total_lines:>25} |")
    lines.append(f"| {'Parsed Entries':<30} | {result.parsed_entries:>25} |")
    if result.parse_errors > 0:
        lines.append(f"| {'Parse Errors':<30} | {result.parse_errors:>25} |")
    
    lines.append("+" + "-" * 58 + "+")
    lines.append("|" + " LOG LEVELS ".center(58) + "|")
    lines.append("+" + "-" * 58 + "+")
    lines.append(f"| {'Level':<20} | {'Count':>15} | {'Percentage':>18} |")
    lines.append("+" + "-" * 58 + "+")
    
    level_order = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "UNKNOWN"]
    for level in level_order:
        count = result.level_counts.get(level, 0)
        if count > 0:
            percentage = (count / result.parsed_entries * 100) if result.parsed_entries > 0 else 0
            lines.append(f"| {level:<20} | {count:>15} | {percentage:>17.1f}% |")
    
    lines.append("+" + "-" * 58 + "+")
    
    if result.error_groups:
        lines.append("|" + " TOP ERROR GROUPS ".center(58) + "|")
        lines.append("+" + "-" * 58 + "+")
        
        for i, group in enumerate(result.error_groups[:5], 1):
            pattern_truncated = group.pattern[:35] if len(group.pattern) > 35 else group.pattern
            lines.append(f"| #{i} {pattern_truncated:<52} |")
            lines.append(f"|    Count: {group.count:<48} |")
            
            if group.first_seen:
                lines.append(f"|    First: {str(group.first_seen)[:50]:<50} |")
            if group.last_seen:
                lines.append(f"|    Last:  {str(group.last_seen)[:50]:<50} |")
            
            lines.append("+" + "-" * 58 + "+")
    
    if result.source_counts:
        lines.append("|" + " TOP SOURCES ".center(58) + "|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| {'Source':<30} | {'Count':>25} |")
        lines.append("+" + "-" * 58 + "+")
        
        for source, count in sorted(result.source_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            source_truncated = source[:28] if len(source) > 28 else source
            lines.append(f"| {source_truncated:<30} | {count:>25} |")
        
        lines.append("+" + "-" * 58 + "+")
    
    return "\n".join(lines)
