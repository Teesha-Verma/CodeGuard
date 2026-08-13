---
id: OWASP-CS-denial-of-service
title: Denial of Service Cheat Sheet
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
  - cheat-sheet
  - denial-of-service
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Defensive practices to mitigate Application Denial of Service (DoS) attacks.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to Denial of Service.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
# VULNERABLE: Executing complex regex matching user input without limits
```

# Good Code Patterns
```python
# SECURE: Limit regex search duration and apply connection limits
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Apply rate-limiting controls.
2. Limit request body sizes.
3. Set timeouts on all read/write connection sockets.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/denial_of_service.html
