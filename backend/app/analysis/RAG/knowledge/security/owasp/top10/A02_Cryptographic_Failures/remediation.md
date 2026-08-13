---
id: OWASP-A02
title: Cryptographic Failures - Remediation
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
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for secure patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
1. Use standardized libraries (e.g. `cryptography` in Python, JCA in Java) rather than implementing custom crypto.
2. Hash passwords using Argon2id, bcrypt, or PBKDF2 with adequate salt and iterations.
3. Always encrypt sensitive data at rest using AES-256-GCM or AES-256-CBC.

# Framework Notes
In Spring Boot, integrate Spring Security's `BCryptPasswordEncoder` or `Argon2PasswordEncoder`. In Python, use `passlib` or `argon2-cffi` for password hashing and validation.

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
