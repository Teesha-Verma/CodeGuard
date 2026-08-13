---
id: OWASP-A01
title: Broken Access Control - Overview
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: critical
priority: high
tags:
  - access-control
  - authorization
  - idor
  - privilege-escalation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A01_2021-Broken_Access_Control/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-22
  - CWE-284
  - CWE-285
  - CWE-639
---

# Overview
Broken Access Control occurs when users can access resources or perform actions outside of their intended permissions. Web applications fail to enforce authorization checks, allowing attackers to access unauthorized data, modify settings, or elevate privileges.

# Why it matters
Access control failures allow attackers to view sensitive records, modify data, assume administrative control, or execute functions restricted to high-privileged roles. This can result in severe data breaches and regulatory compliance violations.

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
OWASP ASVS V3 (Access Control), NIST SP 800-53 AC (Access Control), ISO/IEC 27001 A.9 (Access Control).

# References
1. OWASP Top 10 A01: https://owasp.org/Top10/A01_2021-Broken_Access_Control/
2. OWASP Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
