---
id: OWASP-API3
title: Broken Object Property Level Authorization
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
  - broken-object-property-level-authorization
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-915 (Mass Assignment), OWASP Top 10 A01
---

# Overview
Broken Object Property Level Authorization (BOPLA) occurs when APIs expose properties of objects that should remain hidden, or allow modifying fields they shouldn't.

# Why it matters
Attackers can intercept sensitive information (e.g. password hash or SSN returned in JSON) or overwrite fields like account roles by submitting unauthorized payload parameters.

# Detection Rules
1. Verify endpoints return only requested/allowed fields.
2. Attempt mass assignment by sending additional JSON properties (e.g. `"is_admin": true`).

# Bad Code Patterns
```python
# VULNERABLE: Direct model update allows mass assignment
@app.put('/api/profile')
def update_profile(data: dict, current_user = Depends(get_user)):
    db.update_user(current_user.id, **data)
```

# Good Code Patterns
```python
# SECURE: Use strict schema validators (Pydantic) to limit modifiable fields
class ProfileUpdate(BaseModel):
    bio: str
    display_name: str

@app.put('/api/profile')
def update_profile(data: ProfileUpdate, current_user = Depends(get_user)):
    db.update_user(current_user.id, bio=data.bio, display_name=data.display_name)
```

# Common Mistakes
Returning raw domain entities to the client instead of Data Transfer Objects (DTO).

# Secure Alternatives
Use DTOs or Pydantic models to strictly define response and request serialization schemas.

# Framework Notes
In FastAPI, leverage `response_model` to automatically filter response data.

# Performance Considerations
Querying only required columns from the database (e.g., avoiding `SELECT *`) improves database performance.

# Related Standards
CWE-915 (Mass Assignment), OWASP Top 10 A01

# References
OWASP API Security Top 10: API3:2023
