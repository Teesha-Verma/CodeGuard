---
id: OWASP-A08
title: Software and Data Integrity Failures - Detection
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
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Search code for usage of insecure deserialization functions (e.g. `pickle` in Python, native `ObjectInputStream` in Java).
2. Review CI/CD configurations to verify dependencies and images are verified using signatures/hashes.
3. Audit message queues (e.g. RabbitMQ) for payload validation.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Deserializing user-provided binary arrays, files, or cookies using raw serialization features of programming languages.
2. Pushing software updates or docker base images without validating their checksums or signatures.
3. Using unsigned JSON Web Tokens (JWT) where the server accepts the `none` algorithm.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
JSON/Protocol Buffers parsing is significantly faster and less memory-intensive than Java object serialization or Python's pickle parser.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
