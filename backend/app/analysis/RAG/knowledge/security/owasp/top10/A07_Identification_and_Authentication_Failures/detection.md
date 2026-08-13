---
id: OWASP-A07
title: Identification and Authentication Failures - Detection
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
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Check for lack of brute-force protection (no rate limits, account lockouts).
2. Review password policies for weak complexity requirements.
3. Verify session identifiers are refreshed upon login and properly invalidated on logout.
4. Check if Multi-Factor Authentication (MFA) is absent for administrative portals.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Allowing weak passwords (e.g. `123456`, `password`).
2. Exposing session tokens in URLs (e.g. `http://site.com/dashboard?session_id=XYZ`).
3. Failing to invalidate session tokens on the server when a user logs out.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
MFA and password hashing are computation-heavy. Utilize dedicated caching layers for active sessions to prevent database degradation.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
