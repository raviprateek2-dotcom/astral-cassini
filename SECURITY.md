# Security Policy

## Reporting a Vulnerability

Please report security issues privately by emailing:

- `raviprateek2@gmail.com`

Include:

- Impact summary
- Reproduction steps
- Affected endpoints/files
- Suggested mitigation (if known)

Do not open public GitHub issues for active vulnerabilities.

## Response Expectations

- Acknowledgement target: within 2 business days
- Initial triage target: within 5 business days
- Fix timeline: based on severity and exploitability

## Severity Guidelines

- **Critical**: remote code execution, auth bypass, major data exposure
- **High**: privilege escalation, cross-tenant data access, CSRF/IDOR with real impact
- **Medium**: limited-scope disclosure, moderate hardening gaps
- **Low**: defense-in-depth issues with low exploitability

## Supported Versions

Security updates are prioritized for the latest `master` branch.
