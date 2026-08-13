---
id: OWASP-API7
title: Server Side Request Forgery (SSRF)
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
  - server-side-request-forgery-(ssrf)
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-918, OWASP Top 10 A10
---

# Overview
SSRF occurs when API endpoints fetch remote resources using user-submitted URLs without checking the target destination.

# Why it matters
Attackers force the API server to query internal subnets, local host services, or container metadata configurations.

# Detection Rules
Check if API endpoints accept external URLs and resolve them to internal IP segments.

# Bad Code Patterns
```python
# VULNERABLE: Fetching raw url parameter
@app.post('/api/fetch-logo')
def get_logo(url: str):
    return requests.get(url).content
```

# Good Code Patterns
```python
# SECURE: Strict allowlist and scheme checks
@app.post('/api/fetch-logo')
def get_logo(url: str):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc not in ALLOWED_DOMAINS:
        raise HTTPException(400, "Invalid URL")
    return requests.get(url).content
```

# Common Mistakes
Relying on regex blacklists instead of domain allowlists.

# Secure Alternatives
Apply domain allowlists, resolve hostnames, and block private IP address ranges.

# Framework Notes
Configure internal firewall rules to deny outgoing traffic from container subnets to host metadata services.

# Performance Considerations
Set short request connect timeouts to prevent network socket starvation.

# Related Standards
CWE-918, OWASP Top 10 A10

# References
OWASP API Security Top 10: API7:2023
