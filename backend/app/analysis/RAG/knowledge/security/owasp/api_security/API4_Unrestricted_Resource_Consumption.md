---
id: OWASP-API4
title: Unrestricted Resource Consumption
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
  - unrestricted-resource-consumption
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-770, OWASP Top 10 A05
---

# Overview
Unrestricted Resource Consumption occurs when APIs fail to limit request volumes, file sizes, or resource usage, causing service degradation or complete denial of service.

# Why it matters
Attackers can exploit this to overwhelm servers, exhaust system memory, run up cloud infrastructure costs, or crash databases.

# Detection Rules
1. Verify APIs limit size of uploaded files.
2. Verify rate-limiting is active on all public endpoints.

# Bad Code Patterns
```python
# VULNERABLE: Fetching unbounded pages from database
@app.get('/api/users')
def list_users(limit: int):
    return db.query("SELECT * FROM users LIMIT %s", limit)
```

# Good Code Patterns
```python
# SECURE: Hard limit the maximum page size
@app.get('/api/users')
def list_users(limit: int = 20):
    safe_limit = min(limit, 100)
    return db.query("SELECT * FROM users LIMIT %s", safe_limit)
```

# Common Mistakes
Failing to set timeouts on network requests and database queries.

# Secure Alternatives
Deploy rate-limiters at the gateway level, enforce strict payload limits, and implement pagination.

# Framework Notes
Use ASGI rate limiters in FastAPI or bucket4j in Spring Boot.

# Performance Considerations
Set memory and cpu limits on container runtimes to prevent a single service from crashing the host.

# Related Standards
CWE-770, OWASP Top 10 A05

# References
OWASP API Security Top 10: API4:2023
