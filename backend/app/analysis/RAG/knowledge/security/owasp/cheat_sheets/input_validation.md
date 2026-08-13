---
id: OWASP-CS-input-validation
title: Input Validation Cheat Sheet
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
  - input-validation
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Establishes standard validation workflows for all application inputs.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to Input Validation.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
# VULNERABLE: Direct type parsing without format validation
email = req.args.get('email')
```

# Good Code Patterns
```python
# SECURE: Enforce email regex pattern check
if not re.match(r'^\S+@\S+\.\S+$', email):
    raise ValueError("Invalid email")
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Validate type, range, length, and format.
2. Use allowlists (regex for expected formats).
3. Keep validation layers centralized.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/input_validation.html
