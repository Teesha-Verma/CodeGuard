---
id: OWASP-API9
title: Improper Assets Management
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
  - improper-assets-management
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-1059, OWASP Top 10 A06
---

# Overview
Improper Assets Management is the exposure of deprecated, debug, or undocumented API versions (e.g., leaving `/api/v1/` active alongside `/api/v2/`).

# Why it matters
Attackers focus on older versions of API endpoints that lack recent access control improvements or security checks.

# Detection Rules
Map and index all active API routes. Look for undocumented paths.

# Bad Code Patterns
```python
# VULNERABLE: Leaving insecure deprecated endpoints active without checks
@app.get('/api/v1/user/debug')
def debug_users():
    return db.get_raw_users()
```

# Good Code Patterns
```python
# SECURE: Delete deprecated debug endpoints or enforce admin-only checks
@app.get('/api/v2/user/info', dependencies=[Depends(require_user)])
def get_user_info():
    return db.get_safe_user_data()
```

# Common Mistakes
Failing to document new API endpoints or neglecting decommissioning processes.

# Secure Alternatives
Create an API service register, apply API gateways, and delete old endpoints.

# Framework Notes
Maintain versioning schemes (e.g. prefix routes with `/api/v2/`).

# Performance Considerations
Routing legacy clients to specific deprecation notices reduces main server computation costs.

# Related Standards
CWE-1059, OWASP Top 10 A06

# References
OWASP API Security Top 10: API9:2023
