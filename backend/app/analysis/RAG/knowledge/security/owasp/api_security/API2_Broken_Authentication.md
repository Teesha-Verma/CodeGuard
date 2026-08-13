---
id: OWASP-API2
title: Broken Authentication
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
  - broken-authentication
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-287, OWASP Top 10 A07
---

# Overview
Broken Authentication in APIs refers to weaknesses in authentication flows, tokens (JWT), or session management that allow attackers to assume other users' identities.

# Why it matters
Compromised authentication permits unauthorized API execution, leading to data theft, modification, and execution of sensitive admin actions.

# Detection Rules
1. Review JWT configurations for weak verification keys or usage of the 'none' algorithm.
2. Test API endpoints for credential-stuffing vulnerability (lack of rate-limiting).

# Bad Code Patterns
```python
# VULNERABLE: Accepting JWT without cryptographic signature verification
def verify_token(token):
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload
```

# Good Code Patterns
```python
# SECURE: Enforce signature verification and expiration check
def verify_token(token):
    try:
        return jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
```

# Common Mistakes
Exposing API keys in git repositories or sending session tokens as query parameters.

# Secure Alternatives
Enforce Multi-Factor Authentication (MFA), use OAuth2 token verification, and rotate signature keys regularly.

# Framework Notes
Use Spring Security OAuth2 Resource Server or FastAPI oauth2 schemes to handle JWT verification.

# Performance Considerations
Cache signature verification public keys to avoid fetching them from the JWKS provider on every request.

# Related Standards
CWE-287, OWASP Top 10 A07

# References
OWASP API Security Top 10: API2:2023
