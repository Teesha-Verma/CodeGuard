---
id: OWASP-A08
title: Software and Data Integrity Failures - Overview
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
This vulnerability occurs when code and infrastructure make assumptions about software updates, critical data, or CI/CD pipelines without verifying their integrity. A classic example is insecure deserialization, where untrusted data is converted into objects without verification.

# Why it matters
Attackers can intercept pipeline updates or manipulate serialized object streams to execute arbitrary code (RCE), tamper with data state, or bypass access controls.

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
ASVS V10 (Malicious Code), NIST SP 800-161 (Supply Chain Security).

# References
1. OWASP Top 10 A08: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
2. OWASP Deserialization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
