---
id: OWASP-CS-sql-injection-prevention
title: SQL Injection Prevention Cheat Sheet
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
  - sql-injection-prevention
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Provides guidelines to eliminate SQL Injection (SQLi) vulnerabilities by ensuring commands and parameters remain separated.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to SQL Injection Prevention.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
query = f"SELECT * FROM users WHERE name = '{name}'"
```

# Good Code Patterns
```python
query = "SELECT * FROM users WHERE name = :name"
db.execute(query, {"name": name})
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Use parameterized queries/prepared statements exclusively.
2. Utilize ORMs (SQLAlchemy, Hibernate) correctly.
3. Validate inputs using strict type and pattern validation.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/sql_injection_prevention.html
