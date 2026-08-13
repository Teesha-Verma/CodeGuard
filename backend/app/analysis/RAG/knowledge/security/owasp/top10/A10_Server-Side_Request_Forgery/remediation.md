---
id: OWASP-A10
title: Server-Side Request Forgery - Remediation
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
  - ssrf
  - network-security
  - url-validation
  - allowlist
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-918
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for secure patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
1. Implement a strict allowlist of domains and URL schemes.
2. Isolate network-facing microservices within a separate sandbox, denying access to cloud metadata services.
3. Resolve target domains to IPs and check them against RFC1918 private ranges prior to making requests.

# Framework Notes
Always use a specialized client that disables HTTP redirects or limit the maximum redirects to prevent redirect-based SSRF bypasses.

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
