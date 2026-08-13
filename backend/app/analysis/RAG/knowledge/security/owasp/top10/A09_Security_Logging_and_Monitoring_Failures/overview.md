---
id: OWASP-A09
title: Security Logging and Monitoring Failures - Overview
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
Security Logging and Monitoring Failures occur when applications do not log security-critical events (failed logins, privilege changes), or when logs are not actively monitored. This prevents detection, tracking, and timely containment of active security breaches.

# Why it matters
Without proper logging and monitoring, attackers can maintain persistent access for months before detection. It also prevents forensic analysis during post-incident investigations.

# Detection Rules
*Refer to [detection.md](detection.md) for details on detecting this vulnerability.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
ASVS V7.4 (Security Logging), ISO 27001 A.12.4 (Logging and Monitoring).

# References
1. OWASP Top 10 A09: https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
2. OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
