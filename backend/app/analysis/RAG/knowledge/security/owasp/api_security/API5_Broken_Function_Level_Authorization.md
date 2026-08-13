---
id: OWASP-API5
title: Broken Function Level Authorization
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
  - api-security
  - broken-function-level-authorization
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-285, OWASP Top 10 A01
---

# Overview
Broken Function Level Authorization (BFLA) happens when authorization policies are missing or incorrectly implemented for specific API routes (especially administrative or management functions).

# Why it matters
Attackers can guess admin URL patterns (e.g., swapping `/api/v1/users/` for `/api/v1/admin/users/`) and execute restricted functions (such as deletion or configurations).

# Detection Rules
1. Attempt calling admin endpoints with low-privilege tokens.
2. Review routing paths and verify middleware check functions.

# Bad Code Patterns
```python
# VULNERABLE: No role check validation
@app.delete('/api/admin/users/{user_id}')
def delete_user(user_id: int):
    db.delete(user_id)
```

# Good Code Patterns
```python
# SECURE: Enforce admin role dependency
@app.delete('/api/admin/users/{user_id}', dependencies=[Depends(require_admin_role)])
def delete_user(user_id: int):
    db.delete(user_id)
```

# Common Mistakes
Obfuscating URLs instead of implementing robust server-side access controls.

# Secure Alternatives
Implement role-based or attribute-based access control policies at every API interface.

# Framework Notes
Use Spring Security WebSecurityConfigurerAdapter or FastAPI route dependencies.

# Performance Considerations
Use cached user role lists to prevent double-queries during authorization.

# Related Standards
CWE-285, OWASP Top 10 A01

# References
OWASP API Security Top 10: API5:2023
