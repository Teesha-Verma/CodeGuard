---
id: OWASP-C8
title: Leverage Browser Security Features
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
  - leverage-browser-security-features
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-79, OWASP A05
---

# Overview
Configure application responses with headers (CSP, HSTS) to direct browsers to apply built-in security features.

# Why it matters
Security headers block XSS, clickjacking, and packet sniffing attacks.

# Detection Rules
Examine response headers for security attributes.

# Bad Code Patterns
```python
# VULNERABLE: Missing protection headers
@app.get('/')
def index():
    return "Hello"
```

# Good Code Patterns
```python
# SECURE: Add secure HTTP headers manually or via middleware
@app.get('/')
def index(response: Response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Frame-Options'] = 'DENY'
    return "Hello"
```

# Common Mistakes
Applying permissive Content Security Policies (e.g. allowing `unsafe-inline`).

# Secure Alternatives
Integrate secure headers plugins into reverse proxies (Nginx) or framework setups.

# Framework Notes
Use Spring Security's defaults, which add secure headers automatically.

# Performance Considerations
Configuring security headers at reverse proxies keeps backend response pipelines simple.

# Related Standards
CWE-79, OWASP A05

# References
OWASP Proactive Controls C8
