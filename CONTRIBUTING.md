# Contributing to Log Analyzer CLI

Thank you for your interest in contributing to Log Analyzer CLI! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to follow our code of conduct:

- Be respectful and inclusive
- Accept constructive criticism positively
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

1. **Search existing issues** - Check if the bug has already been reported
2. **Create a new issue** - Use the bug report template
3. **Include details**:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, CLI version)
   - Sample log files if applicable

### Suggesting Features

1. **Search existing proposals** - Check if the feature has been suggested
2. **Create a feature request** - Use the feature request template
3. **Include details**:
   - Clear description of the proposed feature
   - Use cases and motivation
   - Potential implementation approach
   - Any alternative solutions considered

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** - Follow the coding standards
4. **Write tests** - Ensure new code is tested
5. **Update documentation** - Keep docs in sync with code
6. **Submit a pull request** - Use the PR template

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hrachshah/log-analyzer-cli.git
   cd log-analyzer-cli
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

### Coding Standards

- **Style**: Follow PEP 8 with 100 character line length
- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Use Google-style docstrings
- **Testing**: Write tests for all new functionality

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/log_analyzer_cli

# Run specific test file
pytest tests/test_parsers.py
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check code style with flake8
flake8 src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

Example:
```
feat(parsers): Add support for CloudWatch log format

- Added CloudWatchLogsParser class
- Added timestamp parsing for AWS format
- Added tests for new parser

Closes #42
```

## License

By contributing to Log Analyzer CLI, you agree that your contributions will be licensed under the MIT License.

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion

We appreciate all contributions, from bug reports to new features!

## Troubleshooting

### Common Issues

**Q: Large files cause memory issues?**
A: Use streaming mode with `--stream` flag for files over 100MB.

**Q: Log format not detected?**
A: Manually specify format with `--format json|syslog|apache|generic`.

**Q: Gzip compressed files not reading?**
A: Ensure `.gz` extension is present; auto-detection handles gzip.
