---
id: OWASP-CS-cross-site-scripting-prevention
title: Cross-Site Scripting Prevention Cheat Sheet
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
  - cross-site-scripting-prevention
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Details actions to block malicious scripts from executing in client browsers.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to Cross-Site Scripting Prevention.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```html
<div>{{ user_input | safe }}</div>
```

# Good Code Patterns
```html
<div>{{ user_input }}</div> <!-- Automatically escaped by template engine -->
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Perform context-aware output encoding (HTML, Javascript, CSS attributes).
2. Enforce strict Content Security Policy (CSP).
3. Set HttpOnly and Secure cookie parameters.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/cross_site_scripting_prevention.html
