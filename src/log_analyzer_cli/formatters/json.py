"""JSON output formatter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from log_analyzer_cli.analyzer import AnalysisResult


def format_json(result: AnalysisResult, pretty: bool = True) -> str:
    """Format analysis result as JSON.
    
    Args:
        result: Analysis result to format.
        pretty: Whether to pretty-print the JSON.
        
    Returns:
        JSON string.
    """
    output = _result_to_dict(result)
    
    if pretty:
        return json.dumps(output, indent=2, default=str)
    return json.dumps(output, default=str)


def _result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    """Convert analysis result to a dictionary."""
    output = {
        "summary": {
            "total_lines": result.total_lines,
            "parsed_entries": result.parsed_entries,
            "parse_errors": result.parse_errors,
        },
        "level_counts": dict(result.level_counts),
        "error_groups": [],
        "sources": dict(result.source_counts),
    }
    
    for group in result.error_groups:
        error_group = {
            "pattern": group.pattern,
            "count": group.count,
        }
        
        if group.first_seen:
            error_group["first_seen"] = group.first_seen.isoformat()
        if group.last_seen:
            error_group["last_seen"] = group.last_seen.isoformat()
        
        if group.sample_messages:
            error_group["sample_messages"] = group.sample_messages
        
        output["error_groups"].append(error_group)
    
    if result.time_distribution and result.time_distribution.entries:
        try:
            start = min(result.time_distribution.entries)
            end = max(result.time_distribution.entries)
        except TypeError:
            # Mixed naive and aware datetimes — normalize all to UTC for comparison
            normalized = []
            for ts in result.time_distribution.entries:
                if ts.tzinfo is None:
                    normalized.append(ts.replace(tzinfo=timezone.utc))
                else:
                    normalized.append(ts)
            start = min(normalized)
            end = max(normalized)
        output["time_range"] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "total_entries": len(result.time_distribution.entries),
        }
    
    if result.warnings:
        output["warnings"] = result.warnings
    
    return output
