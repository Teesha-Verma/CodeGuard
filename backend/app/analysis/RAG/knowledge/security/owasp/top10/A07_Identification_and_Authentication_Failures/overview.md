---
id: OWASP-A07
title: Identification and Authentication Failures - Overview
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
  - authentication
  - passwords
  - session-management
  - mfa
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-287
  - CWE-307
  - CWE-340
  - CWE-384
---

# Overview
Identification and Authentication Failures occur when applications fail to confirm a user's identity, allowing attackers to hijack sessions, perform credential stuffing, or brute force their way into user accounts.

# Why it matters
Weaknesses in authentication bypass security perimeter defenses, allowing attackers to assume arbitrary identities, view proprietary information, and modify settings.

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
ASVS V2 (Authentication), NIST SP 800-63B (Digital Identity Guidelines).

# References
1. OWASP Top 10 A07: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
2. OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
