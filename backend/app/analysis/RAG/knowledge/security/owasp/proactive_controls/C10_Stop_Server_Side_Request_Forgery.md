---
id: OWASP-C10
title: Stop Server Side Request Forgery
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
  - stop-server-side-request-forgery
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-918, OWASP A10
---

# Overview
Mitigate SSRF risk by validating schemes, allowlisting domains, and resolving DNS target addresses.

# Why it matters
Unrestricted requests allow scanning internal configurations and cloud databases.

# Detection Rules
Locate routes accepting URLs and evaluate validation checks.

# Bad Code Patterns
```python
# VULNERABLE: Direct request to arbitrary host
requests.get(url)
```

# Good Code Patterns
```python
# SECURE: Verify scheme and restrict requests to domain allowlist
parsed = urlparse(url)
if parsed.scheme == 'https' and parsed.netloc in ALLOWED_DOMAINS:
    requests.get(url)
```

# Common Mistakes
Using blacklists or forgetting redirect handling.

# Secure Alternatives
Execute requests inside a separate VPC subnet without internal access.

# Framework Notes
Configure underlying network routers to drop local requests.

# Performance Considerations
Set connection and read timeouts on external API requests.

# Related Standards
CWE-918, OWASP A10

# References
OWASP Proactive Controls C10
