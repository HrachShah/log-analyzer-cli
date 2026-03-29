# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-03-20

### Added
- Initial stable release
- Multi-format log parsing support:
  - Syslog (RFC 3164/5424) format
  - JSON structured logs
  - Apache/Nginx access logs
  - Generic timestamp-based logs
- Core analysis features:
  - Log level distribution analysis
  - Error grouping with pattern normalization
  - Time-based distribution analysis
  - Source/component counting
- Output formatters:
  - Text (human-readable)
  - JSON (machine-readable)
  - Table (formatted ASCII table)
- CLI filtering capabilities:
  - Filter by log level (ERROR, WARNING, INFO, DEBUG, CRITICAL)
  - Regex pattern filtering
  - Time range filtering (start-time, end-time)
- Large file support with streaming
- Gzip compressed file support
- Auto-detection of log format

### Changed
- Upgraded to Click 8.x for CLI framework

### Fixed
- Various parsing edge cases for different log formats

## [0.5.0] - 2025-02-15

### Added
- Beta release with basic functionality
- Initial parser framework
- Basic CLI interface
- Text and JSON output formatters

### Known Issues
- Error grouping sometimes combines unrelated errors
- Limited support for non-standard log formats

## [0.1.0] - 2025-01-10

### Added
- Initial development version
- Basic parser infrastructure
- Prototype CLI with analyze command
