---
id: OWASP-API8
title: Security Misconfiguration
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
  - security-misconfiguration
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-16, OWASP Top 10 A05
---

# Overview
Security Misconfiguration in APIs refers to exposed debug pages, verbose error messages, or insecure transport configurations.

# Why it matters
Attackers gain architectural descriptions, database types, or open connections to execute attacks directly.

# Detection Rules
Scan API paths for CORS allow-all headers, default error outputs, or unencrypted endpoints.

# Bad Code Patterns
```python
# VULNERABLE: CORS allow-all and verbose logs
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

# Good Code Patterns
```python
# SECURE: Limit allowed origins to trusted domains
app.add_middleware(CORSMiddleware, allow_origins=["https://app.domain.com"])
```

# Common Mistakes
Exposing dev/stage API documentation endpoints in production environments.

# Secure Alternatives
Build configuration profiles and perform regular environment scans.

# Framework Notes
Disable swagger endpoints on production profiles in FastAPI.

# Performance Considerations
Apply compression and CORS headers at the load balancer level.

# Related Standards
CWE-16, OWASP Top 10 A05

# References
OWASP API Security Top 10: API8:2023
