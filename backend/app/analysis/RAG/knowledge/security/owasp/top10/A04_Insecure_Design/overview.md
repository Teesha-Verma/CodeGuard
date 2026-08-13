---
id: OWASP-A04
title: Insecure Design - Overview
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
  - design
  - architecture
  - threat-modeling
  - defense-in-depth
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A04_2021-Insecure_Design/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-269
  - CWE-601
  - CWE-657
  - CWE-1173
---

# Overview
Insecure Design represents flaws in architecture and system design rather than implementation bugs. It focuses on the lack of threat modeling, secure design principles, and integration of security controls throughout the entire software lifecycle.

# Why it matters
No amount of secure coding can fix a fundamentally insecure design. Flawed designs allow attackers to abuse business logic, bypass authentication, or exploit weak system flows.

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
NIST SP 800-160 (Systems Security Engineering), ISO/IEC 27034 (Application Security).

# References
1. OWASP Top 10 A04: https://owasp.org/Top10/A04_2021-Insecure_Design/
2. OWASP Threat Modeling Project: https://owasp.org/www-community/Threat_Modeling
