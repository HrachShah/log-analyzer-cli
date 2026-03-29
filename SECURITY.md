# Security Policy

## Supported Versions

The following versions of Log Analyzer CLI are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Log Analyzer CLI, please send an email to security@log-analyzer-cli.dev. All security vulnerabilities will be promptly addressed.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Disclosure Policy

- We follow a **coordinated disclosure** process
- We request that you give us reasonable time to address the vulnerability before public disclosure
- We will credit reporters in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using Log Analyzer CLI:

1. **Input Validation**: Always validate log files before processing
2. **File Access**: Run with minimal required permissions
3. **Sensitive Data**: Be cautious when processing logs containing sensitive information
4. **Output Handling**: Properly handle and secure CLI output

## Security Updates

Security updates will be released as patch versions and announced through:

- GitHub Security Advisories
- Release notes

Thank you for helping keep Log Analyzer CLI secure!
