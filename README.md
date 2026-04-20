# Log Analyzer CLI

[![PyPI Version](https://img.shields.io/pypi/v/log-analyzer-cli)](https://pypi.org/project/log-analyzer-cli/)
[![Python Versions](https://img.shields.io/pypi/pyversions/log-analyzer-cli)](https://pypi.org/project/log-analyzer-cli/)
[![Build Status](https://github.com/hrachshah/log-analyzer-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/hrachshah/log-analyzer-cli/actions)
[![Test Coverage](https://codecov.io/gh/hrachshah/log-analyzer-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/hrachshah/log-analyzer-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready **Python CLI tool** for analyzing log files, summarizing errors, warnings, and key metrics. Designed for DevOps, SRE, and developers who need to quickly understand what's happening in their log files.

## Features

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

## Installation

### From PyPI (Recommended)

```bash
pip install log-analyzer-cli
```

### From Source

```bash
git clone https://github.com/hrachshah/log-analyzer-cli.git
cd log-analyzer-cli
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

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

## Usage

### Commands

#### `analyze`

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
# Basic analysis
log-analyzer-cli analyze /var/log/syslog

# JSON output
log-analyzer-cli analyze /var/log/app.log -o json

# Filter errors and warnings only
log-analyzer-cli analyze /var/log/app.log -l ERROR,WARNING

# Search for specific pattern
log-analyzer-cli analyze /var/log/app.log -p "database.*failed"

# Time-based filtering
log-analyzer-cli analyze /var/log/app.log --start-time "2025-03-20 10:00:00" --end-time "2025-03-20 12:00:00"

# Verbose output with error details
log-analyzer-cli analyze /var/log/app.log -v
```

#### `formats`

List supported log formats.

```bash
log-analyzer-cli formats
```

### Examples

#### Analyzing a Syslog File

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

#### Analyzing JSON Logs

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

#### Analyzing Apache Access Logs

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

## Configuration

### Log Format Detection

Log Analyzer CLI automatically detects the log format based on the content. You can also manually specify the format using the `--format` option:

- `auto` - Automatically detect format (default)
- `json` - JSON structured logs
- `syslog` - Syslog format
- `apache` - Apache/Nginx access logs
- `generic` - Generic timestamp-based logs

### Environment Variables

No environment variables are required. All configuration is done via command-line options.

## Project Structure

```
log-analyzer-cli/
├── src/log_analyzer_cli/          # Main package
│   ├── __init__.py               # Package initialization
│   ├── cli.py                    # CLI entry point
│   ├── analyzer.py               # Core analysis logic
│   ├── utils.py                  # Utility functions
│   ├── parsers/                  # Log format parsers
│   │   ├── base.py              # Base parser class
│   │   ├── syslog.py           # Syslog parser
│   │   ├── json_log.py         # JSON log parser
│   │   ├── apache.py           # Apache/Nginx parser
│   │   └── generic.py          # Generic parser
│   └── formatters/              # Output formatters
│       ├── text.py              # Text formatter
│       ├── json.py              # JSON formatter
│       └── table.py             # Table formatter
├── tests/                        # Test suite
│   ├── test_parsers.py
│   ├── test_analyzer.py
│   └── test_cli.py
├── examples/                      # Example log files
│   ├── syslog-sample.log
│   ├── app-json.log
│   ├── apache-sample.log
│   ├── mixed.log
│   └── error-heavy.log
├── .github/                       # GitHub configuration
│   ├── workflows/                # CI/CD workflows
│   └── ISSUE_TEMPLATE/           # Issue templates
├── pyproject.toml                # Package configuration
├── README.md                      # This file
├── CHANGELOG.md                   # Version history
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
└── SECURITY.md                   # Security policy
```

## Development

### Requirements

- Python 3.10+
- click>=8.0.0

### Development Requirements

- pytest>=7.0.0
- pytest-cov>=4.0.0
- black>=23.0.0
- mypy>=1.0.0
- flake8>=6.0.0

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [lnav](https://lnav.org/) - Advanced log file viewer
- [goaccess](https://goaccess.io/) - Real-time web log analyzer
- [flog](https://github.com/mingrammer/flog) - Fake log generator

## Keywords

log analyzer, log parser, cli tool, syslog, json logs, apache logs, error analysis, log metrics, devops, sre, logging
fix
# Zo Bot Contribution
