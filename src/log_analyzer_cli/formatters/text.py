"""Text output formatter."""

from __future__ import annotations

from log_analyzer_cli.analyzer import AnalysisResult, ErrorGroup, TimeDistribution


def format_text(result: AnalysisResult, verbose: bool = False) -> str:
    """Format analysis result as human-readable text.
    
    Args:
        result: Analysis result to format.
        verbose: Include more detailed output.
        
    Returns:
        Formatted text string.
    """
    lines = []
    
    lines.append("=" * 60)
    lines.append("LOG ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append(f"Total Lines:     {result.total_lines}")
    lines.append(f"Parsed Entries:  {result.parsed_entries}")
    if result.parse_errors > 0:
        lines.append(f"Parse Errors:    {result.parse_errors}")
    lines.append("")
    
    lines.append("-" * 40)
    lines.append("LOG LEVEL DISTRIBUTION")
    lines.append("-" * 40)
    
    level_order = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "UNKNOWN"]
    for level in level_order:
        count = result.level_counts.get(level, 0)
        if count > 0:
            percentage = (count / result.parsed_entries * 100) if result.parsed_entries > 0 else 0
            lines.append(f"  {level:10} : {count:6} ({percentage:5.1f}%)")
    lines.append("")
    
    if result.error_groups:
        lines.append("-" * 40)
        lines.append("TOP ERROR GROUPS")
        lines.append("-" * 40)
        
        for i, group in enumerate(result.error_groups[:10], 1):
            lines.append(f"\n{i}. Pattern: {group.pattern[:60]}")
            lines.append(f"   Count: {group.count}")
            
            if group.first_seen and group.last_seen:
                time_range = f"{group.first_seen} to {group.last_seen}"
                lines.append(f"   Time Range: {time_range}")
            
            if group.sample_messages and verbose:
                lines.append("   Sample messages:")
                for msg in group.sample_messages[:3]:
                    lines.append(f"     - {msg[:80]}")
        
        lines.append("")
    
    if result.source_counts and verbose:
        lines.append("-" * 40)
        lines.append("SOURCES")
        lines.append("-" * 40)
        
        for source, count in sorted(result.source_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {source:30} : {count:6}")
        
        lines.append("")
    
    if result.time_distribution and verbose:
        lines.append("-" * 40)
        lines.append("TIME DISTRIBUTION")
        lines.append("-" * 40)
        
        intervals = _calculate_time_intervals(result.time_distribution)
        if intervals:
            for interval, count in intervals:
                lines.append(f"  {interval:25} : {count:6}")
        
        lines.append("")
    
    if result.warnings:
        lines.append("-" * 40)
        lines.append("WARNINGS")
        lines.append("-" * 40)
        for warning in result.warnings:
            lines.append(f"  - {warning}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def _calculate_time_intervals(dist: TimeDistribution) -> list[tuple[str, int]]:
    """Calculate counts per time interval."""
    if not dist.entries:
        return []
    
    intervals: dict[str, int] = {}
    interval = dist.interval_minutes
    
    for ts in dist.entries:
        minute_bucket = (ts.minute // interval) * interval
        key = ts.strftime(f"%Y-%m-%d %H:{minute_bucket:02d}")
        intervals[key] = intervals.get(key, 0) + 1
    
    return sorted(intervals.items(), key=lambda x: x[0])
