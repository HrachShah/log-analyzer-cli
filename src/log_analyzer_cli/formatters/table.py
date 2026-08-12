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
    INNER_WIDTH = 58

    def _border() -> str:
        return "+" + "-" * INNER_WIDTH + "+"

    def _section(title: str) -> str:
        return "|" + f" {title} ".center(INNER_WIDTH) + "|"

    def _row(cells: list[str], widths: list[int], aligns: list[str]) -> str:
        parts = []
        for cell, width, align in zip(cells, widths, aligns):
            if align == "left":
                parts.append(" " + str(cell).ljust(width - 1))
            else:
                parts.append(str(cell).rjust(width))
        return "|" + "|".join(parts) + "|"

    lines = []

    lines.append(_border())
    lines.append(_section("LOG ANALYSIS SUMMARY"))
    lines.append(_border())

    summary_widths = [31, 27]
    summary_aligns = ["left", "right"]
    lines.append(_row(["Metric", "Value"], summary_widths, summary_aligns))
    lines.append(_border())

    lines.append(_row(["Total Lines", result.total_lines], summary_widths, summary_aligns))
    lines.append(_row(["Parsed Entries", result.parsed_entries], summary_widths, summary_aligns))
    if result.parse_errors > 0:
        lines.append(_row(["Parse Errors", result.parse_errors], summary_widths, summary_aligns))

    lines.append(_border())
    lines.append(_section("LOG LEVELS"))
    lines.append(_border())

    level_widths = [21, 16, 19]
    level_aligns = ["left", "right", "right"]
    lines.append(_row(["Level", "Count", "Percentage"], level_widths, level_aligns))
    lines.append(_border())

    level_order = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "UNKNOWN"]
    for level in level_order:
        count = result.level_counts.get(level, 0)
        if count > 0:
            percentage = (count / result.parsed_entries * 100) if result.parsed_entries > 0 else 0
            lines.append(_row([level, count, f"{percentage:.1f}%"], level_widths, level_aligns))

    lines.append(_border())

    if result.error_groups:
        lines.append(_section("TOP ERROR GROUPS"))
        lines.append(_border())

        for i, group in enumerate(result.error_groups[:5], 1):
            pattern_truncated = group.pattern[:54] if len(group.pattern) > 54 else group.pattern
            pattern_field = f" #{i} {pattern_truncated}".ljust(INNER_WIDTH)
            lines.append(f"|{pattern_field}|")
            count_field = f"    Count: {group.count}".ljust(INNER_WIDTH)
            lines.append(f"|{count_field}|")

            if group.first_seen:
                first_str = str(group.first_seen)[:44]
                first_field = f"    First: {first_str}".ljust(INNER_WIDTH)
                lines.append(f"|{first_field}|")
            if group.last_seen:
                last_str = str(group.last_seen)[:44]
                last_field = f"    Last:  {last_str}".ljust(INNER_WIDTH)
                lines.append(f"|{last_field}|")

            lines.append(_border())

    if result.source_counts:
        lines.append(_section("TOP SOURCES"))
        lines.append(_border())
        lines.append(_row(["Source", "Count"], summary_widths, summary_aligns))
        lines.append(_border())

        for source, count in sorted(result.source_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            source_truncated = source[:29] if len(source) > 29 else source
            lines.append(_row([source_truncated, count], summary_widths, summary_aligns))

        lines.append(_border())

    return "\n".join(lines)
