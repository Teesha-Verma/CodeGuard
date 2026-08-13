---
id: OWASP-C2
title: Use Cryptography the Proper Way
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
  - proactive-control
  - use-cryptography-the-proper-way
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-327, OWASP A02
---

# Overview
Protect sensitive data using strong cryptographic algorithms and proper key management.

# Why it matters
Compromised keys or weak algorithms allow decryption of passwords, credentials, and data.

# Detection Rules
Scan code for weak algorithms (MD5, DES) and verify secret management policies.

# Bad Code Patterns
```python
# VULNERABLE: Hardcoded weak encryption key
cipher = AES.new('weakkey123456789', AES.MODE_ECB)
```

# Good Code Patterns
```python
# SECURE: High-entropy key loaded from environment and secure mode GCM
cipher = AES.new(os.environ['AES_KEY'], AES.MODE_GCM, nonce=nonce)
```

# Common Mistakes
Creating proprietary cryptographic formulas or reusing salts/nonces.

# Secure Alternatives
Use Standard Cryptographic Libraries (e.g. PyCryptodome, JCA) and KMS (Key Management Services).

# Framework Notes
Leverage framework configuration parameters for secure hash settings.

# Performance Considerations
Prefer AES-GCM for hardware-accelerated decryption efficiency.

# Related Standards
CWE-327, OWASP A02

# References
OWASP Proactive Controls C2
