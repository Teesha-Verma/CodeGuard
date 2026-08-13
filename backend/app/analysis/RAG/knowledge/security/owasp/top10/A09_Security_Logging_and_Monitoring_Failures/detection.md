---
id: OWASP-A09
title: Security Logging and Monitoring Failures - Detection
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: medium
priority: medium
tags:
  - logging
  - monitoring
  - audit-logs
  - siem
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-117
  - CWE-778
  - CWE-779
---

# Overview
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Check if security-critical actions (logins, authorization failures, data updates) fail to generate logs.
2. Inspect logs for presence of sensitive data (passwords, session keys, credit card numbers).
3. Audit alerts and monitoring tools to ensure threshold violations trigger notifications.
4. Check if logs are stored strictly locally without centralization.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Logging plaintext passwords or PII (e.g. social security numbers, credit card tokens).
2. Writing logs to local files without shipping them to a secure, centralized log management platform (SIEM).
3. Setting log levels too high (e.g., only logging `FATAL` errors), missing critical security warnings (`WARN`).

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Perform logging asynchronously using queues (e.g. Logback's `AsyncAppender`) to avoid blocking request threads during disk write operations.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
