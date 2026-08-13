---
id: OWASP-A02
title: Cryptographic Failures - Overview
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
  - cryptography
  - encryption
  - hashing
  - sensitive-data
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-311
  - CWE-327
  - CWE-328
  - CWE-757
---

# Overview
Cryptographic Failures occur when sensitive data is exposed or compromised due to absent or weak cryptographic protections in transit and at rest. This includes weak cipher algorithms, hardcoded secret keys, and insufficient key protection.

# Why it matters
If sensitive data (passwords, credit card numbers, PII) is stored or transmitted without strong encryption, attackers who gain access to the database or intercept network traffic can read, steal, or tamper with the data, causing severe security breaches.

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
ASVS V2 (Communications Security), FIPS 140-3, PCI-DSS Requirement 3 (Protect stored cardholder data).

# References
1. OWASP Top 10 A02: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
2. OWASP Cryptographic Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
