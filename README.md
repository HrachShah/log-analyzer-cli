README: updated

[![PyPI Version](https://img.shields.io/pypi/v/log-analyzer-cli)](https://pypi.org/project/log-analyzer-cli/)
[![Python Versions](https://img.shields.io/pypi/pyversions/log-analyzer-cli)](https://pypi.org/project/log-analyzer-cli/)
[![Build Status](https://github.com/hrachshah/log-analyzer-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/hrachshah/log-analyzer-cli/actions)
[![Test Coverage](https://codecov.io/gh/hrachshah/log-analyzer-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/hrachshah/log-analyzer-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready **Python CLI tool** for analyzing log files, summarizing errors, warnings, and key metrics. Designed for DevOps, SRE, and developers who need to quickly understand what's happening in their log files.

README: updated# Features

- **Multi-format Log Parsing**: Automatic detection and parsing of:
  - Syslog (RFC 3164/5424)
  - JSON structured logs (cloud-native formats)
  - Apache/Nginx access logs
  - Generic timestamp-based logs
- **Intelligent Analysis**:
  - Log level distribution (ERROR, WARNING, INFO, DEBUG, CRITICAL)
  - Error grouping with pattern normalization
  - Time-based distribution analysis
  - Source/component counting
- **Flexible Output**:
  - Text (human-readable)
  - JSON (machine-readable, perfect for automation)
  - Table (ASCII formatted)
- **Powerful Filtering**:
  - Filter by log level
  - Regex pattern matching
  - Time range filtering
- **Performance**:
  - Streaming for large files
  - Gzip compressed file support
  - Auto-detection of log format

README: updated# Installation

README: updated## From PyPI (Recommended)

```bash
pip install log-analyzer-cli
```

README: updated## From Source

```bash
git clone https://github.com/hrachshah/log-analyzer-cli.git
cd log-analyzer-cli
pip install -e .
```

README: updated## Development Installation

```bash
pip install -e ".[dev]"
```

README: updated# Quick Start

Analyze a log file with default settings:

```bash
log-analyzer-cli analyze /var/log/syslog
```

Output to JSON format:

```bash
log-analyzer-cli analyze /var/log/syslog -o json
```

Filter by log level:

```bash
log-analyzer-cli analyze /var/log/syslog -l ERROR,WARNING
```

README: updated# Usage

README: updated## Commands

README: updated### `analyze`

Analyze a log file and summarize errors, warnings, and metrics.

```bash
log-analyzer-cli analyze [OPTIONS] FILE
```

**Options:**

| Option | Description |
|--------|-------------|
| `-f, --format` | Log format (auto, json, syslog, apache, generic) |
| `-o, --output` | Output format (text, json, table) |
| `-v, --verbose` | Include detailed output |
| `--no-group` | Disable error grouping |
| `-l, --levels` | Comma-separated list of log levels to include |
| `-p, --pattern` | Regex pattern to filter log lines |
| `--start-time` | Filter entries after this timestamp (YYYY-MM-DD HH:MM:SS) |
| `--end-time` | Filter entries before this timestamp (YYYY-MM-DD HH:MM:SS) |

**Examples:**

```bash
README: updated
log-analyzer-cli analyze /var/log/syslog

README: updated
log-analyzer-cli analyze /var/log/app.log -o json

README: updated warnings only
log-analyzer-cli analyze /var/log/app.log -l ERROR,WARNING

README: updated pattern
log-analyzer-cli analyze /var/log/app.log -p "database.*failed"

README: updated-based filtering
log-analyzer-cli analyze /var/log/app.log --start-time "2025-03-20 10:00:00" --end-time "2025-03-20 12:00:00"

README: updated error details
log-analyzer-cli analyze /var/log/app.log -v
```

README: updated### `formats`

List supported log formats.

```bash
log-analyzer-cli formats
```

README: updated## Examples

README: updated### Analyzing a Syslog File

```bash
$ log-analyzer-cli analyze examples/syslog-sample.log

============================================================
LOG ANALYSIS REPORT
============================================================

Total Lines:     32
Parsed Entries:  32

----------------------------------------
LOG LEVEL DISTRIBUTION
----------------------------------------
  CRITICAL   :      1 (  3.1%)
  ERROR      :     10 ( 31.2%)
  WARNING    :      5 ( 15.6%)
  INFO       :     16 ( 50.0%)

----------------------------------------
TOP ERROR GROUPS
----------------------------------------

1. Pattern: <NUM><NUM> kernel: <NUM><NUM><NUM> Out of memory
   Count: 1
   Time Range: 2025-03-20 10:30:00 to 2025-03-20 10:30:00

2. Pattern: systemd<NUM>: Failed to start Application Service
   Count: 1
...

============================================================
```

README: updated### Analyzing JSON Logs

```bash
$ log-analyzer-cli analyze examples/app-json.log -o json
{
  "summary": {
    "total_lines": 32,
    "parsed_entries": 32,
    "parse_errors": 0
  },
  "level_counts": {
    "INFO": 14,
    "DEBUG": 5,
    "WARNING": 4,
    "ERROR": 8,
    "CRITICAL": 1
  },
  "error_groups": [...]
}
```

README: updated### Analyzing Apache Access Logs

```bash
$ log-analyzer-cli analyze examples/apache-sample.log -o table
+------------------------------------------------------------+
|                     LOG ANALYSIS SUMMARY                   |
+------------------------------------------------------------+
| Metric                          |                     Value |
+------------------------------------------------------------+
| Total Lines                    |                        32 |
| Parsed Entries                 |                        32 |
+------------------------------------------------------------+
...
```

README: updated# Configuration

README: updated## Log Format Detection

Log Analyzer CLI automatically detects the log format based on the content. You can also manually specify the format using the `--format` option:

- `auto` - Automatically detect format (default)
- `json` - JSON structured logs
- `syslog` - Syslog format
- `apache` - Apache/Nginx access logs
- `generic` - Generic timestamp-based logs

README: updated## Environment Variables

No environment variables are required. All configuration is done via command-line options.

README: updated# Project Structure

```
log-analyzer-cli/
├── src/log_analyzer_cli/          README: updated
│   ├── __init__.py               README: updated
│   ├── cli.py                    README: updated
│   ├── analyzer.py               README: updated
│   ├── utils.py                  README: updated
│   ├── parsers/                  README: updated
│   │   ├── base.py              README: updated
│   │   ├── syslog.py           README: updated
│   │   ├── json_log.py         README: updated
│   │   ├── apache.py           README: updated/Nginx parser
│   │   └── generic.py          README: updated
│   └── formatters/              README: updated
│       ├── text.py              README: updated
│       ├── json.py              README: updated
│       └── table.py             README: updated
├── tests/                        README: updated
│   ├── test_parsers.py
│   ├── test_analyzer.py
│   └── test_cli.py
├── examples/                      README: updated
│   ├── syslog-sample.log
│   ├── app-json.log
│   ├── apache-sample.log
│   ├── mixed.log
│   └── error-heavy.log
├── .github/                       README: updated
│   ├── workflows/                README: updated/CD workflows
│   └── ISSUE_TEMPLATE/           README: updated
├── pyproject.toml                README: updated
├── README.md                      README: updated
├── CHANGELOG.md                   README: updated
├── CONTRIBUTING.md                README: updated
├── LICENSE                        README: updated
└── SECURITY.md                   README: updated
```

README: updated# Development

README: updated## Requirements

- Python 3.10+
- click>=8.0.0

README: updated## Development Requirements

- pytest>=7.0.0
- pytest-cov>=4.0.0
- black>=23.0.0
- mypy>=1.0.0
- flake8>=6.0.0

README: updated## Running Tests

```bash
pytest tests/
```

README: updated## Code Formatting

```bash
black src/ tests/
```

README: updated## Type Checking

```bash
mypy src/
```

README: updated# Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

README: updated# License

MIT License - see [LICENSE](LICENSE) file for details.

README: updated# Related Projects

- [lnav](https://lnav.org/) - Advanced log file viewer
- [goaccess](https://goaccess.io/) - Real-time web log analyzer
- [flog](https://github.com/mingrammer/flog) - Fake log generator

README: updated# Keywords

log analyzer, log parser, cli tool, syslog, json logs, apache logs, error analysis, log metrics, devops, sre, logging
fix
README: updated
