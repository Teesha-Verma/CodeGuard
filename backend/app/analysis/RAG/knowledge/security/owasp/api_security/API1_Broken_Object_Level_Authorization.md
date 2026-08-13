---
id: OWASP-API1
title: Broken Object Level Authorization
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
  - broken-object-level-authorization
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-639 (Insecure Direct Object Reference), OWASP Top 10 A01
---

# Overview
Broken Object Level Authorization (BOLA) occurs when an application exposes endpoints that access objects by ID but fails to validate that the requester has permissions to access those specific objects.

# Why it matters
BOLA allows attackers to easily harvest or modify other users' sensitive information by enumerating identifiers in URL parameters or request bodies (e.g., changing `/api/v1/user/1001` to `/api/v1/user/1002`).

# Detection Rules
1. Check if ID parameters can be manipulated to access records belonging to other accounts.
2. Use SAST to verify that access control checks check object-level owner attributes against user ID context.

# Bad Code Patterns
```python
@app.get('/api/orders/{order_id}')
def get_order(order_id: int):
    # VULNERABLE: Loads order directly without validating ownership
    return db.query_order(order_id)
```

# Good Code Patterns
```python
@app.get('/api/orders/{order_id}')
def get_order(order_id: int, current_user = Depends(get_current_user)):
    order = db.query_order(order_id)
    # SECURE: Validate ownership before returning object
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order
```

# Common Mistakes
Relying on client-provided ownership flags or assuming that checking login authentication is sufficient to protect specific records.

# Secure Alternatives
Use randomized UUIDs for resource identifiers and implement authorization filters checking access tokens against resource owner mappings in the database.

# Framework Notes
Use custom FastAPI decorators or Spring Boot interceptors to load objects and perform authorization checks before handler methods execute.

# Performance Considerations
Index owner relationship fields in database tables to keep ownership lookups fast.

# Related Standards
CWE-639 (Insecure Direct Object Reference), OWASP Top 10 A01

# References
OWASP API Security Top 10: API1:2023
