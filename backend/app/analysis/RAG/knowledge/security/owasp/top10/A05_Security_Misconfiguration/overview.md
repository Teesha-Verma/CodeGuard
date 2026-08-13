---
id: OWASP-A05
title: Security Misconfiguration - Overview
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
  - misconfiguration
  - hardening
  - headers
  - defaults
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-2
  - CWE-16
  - CWE-200
  - CWE-611
---

# Overview
Security Misconfiguration happens when security controls are poorly configured, left at default settings, or misaligned with best practices. This includes leaving debug modes active, exposing verbose error stack traces, and failing to configure secure HTTP headers.

# Why it matters
Misconfigurations allow attackers to gather system banners, stack traces, and internal URLs, providing blueprints of application architectures. Default credentials and open ports allow immediate unauthorized entry.

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
ASVS V14 (Configuration Security), CIS Benchmarks, NIST SP 800-123 (Securing Public Web Servers).

# References
1. OWASP Top 10 A05: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
2. OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
