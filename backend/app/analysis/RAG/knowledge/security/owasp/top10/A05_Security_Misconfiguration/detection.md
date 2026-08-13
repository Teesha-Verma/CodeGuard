---
id: OWASP-A05
title: Security Misconfiguration - Detection
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
  - misconfiguration
  - hardening
  - headers
  - defaults
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-2
  - CWE-16
  - CWE-200
  - CWE-611
---

# Overview
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Inspect environment config files for active debug modes in production.
2. Scan applications for missing security headers (e.g. CSP, HSTS, X-Content-Type-Options).
3. Audit network security groups and container configurations to ensure only required ports are exposed.
4. Check for default configurations in database and web server instances.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Exposing database management panels (e.g. pgAdmin) or Swagger UI on public networks without authentication.
2. Allowing permissive Cross-Origin Resource Sharing (CORS) headers (e.g. `Access-Control-Allow-Origin: *`) for authenticated endpoints.
3. Using default database ports with default admin accounts (e.g. `postgres/postgres`).

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Configuring static security headers on the reverse proxy/CDN layer (e.g. Cloudflare, CloudFront) reduces load on application servers.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
