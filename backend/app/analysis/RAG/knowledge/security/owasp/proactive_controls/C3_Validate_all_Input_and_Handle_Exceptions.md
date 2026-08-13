---
id: OWASP-C3
title: Validate all Input and Handle Exceptions
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: medium
priority: medium
tags:
  - proactive-control
  - validate-all-input-and-handle-exceptions
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-20, OWASP A03
---

# Overview
Sanitize and validate all incoming data fields before processing or storing them, and ensure errors do not disclose system details.

# Why it matters
Invalid input causes injection, cross-site scripting, and application crashes. Raw exceptions expose configuration blueprints.

# Detection Rules
Examine input controllers for validator integrations. Check exception handlers for raw stack trace outputs.

# Bad Code Patterns
```python
# VULNERABLE: Direct access to payload parameters
def process_age(req):
    return int(req.params.get('age'))
```

# Good Code Patterns
```python
# SECURE: Strict validation range check and type coercion
def process_age(req):
    age_raw = req.params.get('age')
    if not age_raw.isdigit():
        raise ValueError("Invalid format")
    age = int(age_raw)
    if age < 0 or age > 120:
        raise ValueError("Invalid range")
    return age
```

# Common Mistakes
Relying strictly client side or trying to construct blacklist filters.

# Secure Alternatives
Apply schema-based validation libraries (Pydantic, Hibernate Validator) and write centralized error handlers.

# Framework Notes
FastAPI does type and validation using Pydantic parameters automatically.

# Performance Considerations
Keep validation steps lightweight. Cache complex regex compilation patterns.

# Related Standards
CWE-20, OWASP A03

# References
OWASP Proactive Controls C3
