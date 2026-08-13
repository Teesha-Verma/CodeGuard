---
id: OWASP-A02
title: Cryptographic Failures - Detection
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
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Scan code for hardcoded passwords, API keys, or secret tokens.
2. Review cryptographic configurations to identify weak hash functions (MD5, SHA1) or obsolete ciphers (DES, RC4).
3. Check TLS configurations on servers to ensure HTTP is disabled and strong cipher suites are enforced.
4. Use SAST tools to flag insecure random number generators (e.g. using `random` instead of `secrets`).

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Storing passwords using reversible encryption instead of salted, one-way hashes.
2. Generating cryptographic keys with insufficient entropy or predictable seeds.
3. Using HTTP for administrative panels or web service APIs, allowing sniffing of session tokens.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Argon2 and bcrypt are deliberately CPU-intensive to resist brute-force attacks. Tune work factors (iterations/memory) to balance security and responsiveness.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
