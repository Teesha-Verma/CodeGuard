---
id: OWASP-A08
title: Software and Data Integrity Failures - Remediation
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: high
priority: high
tags:
  - integrity
  - deserialization
  - ci-cd
  - signatures
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-502
  - CWE-494
  - CWE-829
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
1. Use standardized data serialization formats (like JSON, YAML, Protocol Buffers) that don't allow arbitrary code execution.
2. Cryptographically sign serialized payloads using HMAC or asymmetric keys before transmission.
3. Implement software signing pipelines and verify components using SCA.

# Framework Notes
Avoid native Java serialization at all costs. In Python, replace `pickle` or `marshal` with `pydantic` and JSON parsing.

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
