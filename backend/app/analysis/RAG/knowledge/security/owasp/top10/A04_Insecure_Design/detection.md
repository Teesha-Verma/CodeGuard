---
id: OWASP-A04
title: Insecure Design - Detection
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
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Review architectural diagrams and threat models to assess logical flaws.
2. Evaluate design specifications for single points of failure or lack of defense-in-depth.
3. Review business logic flows (e.g. registration, password reset) for logical bypasses.
4. Audit privilege models and segregation of duties.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Storing security questions in plaintext or relying on questions that can be guessed using OSINT.
2. Designing applications without error boundaries, leading to cascade failures.
3. Assuming internal systems do not require authentication or authorization.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Design rate-limiting policies at the API gateway layer (e.g. Nginx, Kong) to prevent resource exhaustion without burdening backend application instances.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
