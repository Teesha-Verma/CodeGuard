---
id: OWASP-C7
title: Implement Digital Identity
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
  - implement-digital-identity
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-287, OWASP A07
---

# Overview
Implement secure authentication systems to confirm identity and safely coordinate sessions.

# Why it matters
Authentication failures allow session theft and credential bypasses.

# Detection Rules
Verify cookies possess HttpOnly, Secure, and SameSite parameters. Check brute force protections.

# Bad Code Patterns
```python
# VULNERABLE: Insecure cookies
response.set_cookie('session', user_id)
```

# Good Code Patterns
```python
# SECURE: Secure session cookie attributes
response.set_cookie('session', session_id, httponly=True, secure=True, samesite='Strict')
```

# Common Mistakes
Allowing weak passwords or exposing tokens in HTTP headers or URLs.

# Secure Alternatives
Implement Multi-Factor Authentication (MFA) and secure identity providers (SAML, OIDC).

# Framework Notes
Use Spring Security session controls or FastAPI Security dependencies.

# Performance Considerations
Utilize memory stores like Redis for rapid validation of active sessions.

# Related Standards
CWE-287, OWASP A07

# References
OWASP Proactive Controls C7
