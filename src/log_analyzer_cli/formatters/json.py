"""JSON output formatter."""

from __future__ import annotations

import json
from datetime import datetime
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
        # The parsers can return a mix of naive and tz-aware datetimes when
        # a log file contains both shapes (e.g. one entry from a
        # 2025-03-20 10:15:32 line and another from a 2025-03-20T10:15:33Z
        # line in the same file). ``min()`` / ``max()`` raise
        # ``TypeError: can't compare offset-naive and offset-aware datetimes``
        # in that case, which would prevent the user from getting *any* JSON
        # report. Coerce the naive entries to the same tz-awareness as the
        # first entry before computing the range.
        entries = result.time_distribution.entries
        try:
            start = min(entries).isoformat()
            end = max(entries).isoformat()
        except TypeError:
            anchor = entries[0]
            normalized = [
                e if e.tzinfo is not None and anchor.tzinfo is not None
                else e.replace(tzinfo=anchor.tzinfo)
                if e.tzinfo is None
                else e.replace(tzinfo=None)
                for e in entries
            ]
            start = min(normalized).isoformat()
            end = max(normalized).isoformat()
        output["time_range"] = {
            "start": start,
            "end": end,
            "total_entries": len(entries),
        }
    
    if result.warnings:
        output["warnings"] = result.warnings
    
    return output
