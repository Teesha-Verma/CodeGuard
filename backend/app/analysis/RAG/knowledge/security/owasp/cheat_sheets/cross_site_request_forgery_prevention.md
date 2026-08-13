---
id: OWASP-CS-cross-site-request-forgery-prevention
title: Cross-Site Request Forgery Prevention Cheat Sheet
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
  - cross-site-request-forgery-prevention
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Establishes defense mechanisms to prevent attackers from sending unauthorized commands from a user's browser.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to Cross-Site Request Forgery Prevention.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
# VULNERABLE: API processes POST request without validating CSRF token
```

# Good Code Patterns
```python
# SECURE: Validate CSRF tokens on all state-changing requests (POST, PUT, DELETE)
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Implement double submit cookie patterns or synchronize tokens.
2. Apply `SameSite=Strict` cookie policies.
3. Protect sensitive endpoints behind re-authentication steps.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/cross_site_request_forgery_prevention.html
