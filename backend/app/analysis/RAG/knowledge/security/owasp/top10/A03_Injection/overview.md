---
id: OWASP-A03
title: Injection - Overview
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
  - injection
  - sqli
  - command-injection
  - input-validation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A03_2021-Injection/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-78
  - CWE-89
  - CWE-94
  - CWE-562
---

# Overview
Injection vulnerabilities occur when untrusted user input is sent to an interpreter as part of a command or query. The attacker's hostile data tricks the interpreter into executing unintended commands or accessing data without proper authorization.

# Why it matters
Injection can result in data loss, corruption, disclosure to unauthorized parties, lack of accountability, or denial of service. In severe cases, SQL injection can lead to database takeover, and OS command injection can lead to remote code execution.

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
ASVS V5 (Validation, Sanitization and Encoding), PCI-DSS Requirement 6.5.1 (Injection vulnerabilities).

# References
1. OWASP Top 10 A03: https://owasp.org/Top10/A03_2021-Injection/
2. OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
