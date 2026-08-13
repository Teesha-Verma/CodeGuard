---
id: OWASP-A10
title: Server-Side Request Forgery - Detection
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
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Audit endpoints that accept URLs as parameters (e.g., file upload from link, webhook setup).
2. Test using DNS tracking services (e.g., Interactsh) to confirm out-of-band network calls.
3. Check if server allows requests to loopback addresses (`127.0.0.1`, `localhost`) or private network ranges.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Implementing blacklist validation filters (e.g., blocking `127.0.0.1` but failing to block decimal equivalents like `2130706433` or DNS redirects).
2. Permitting arbitrary protocols (e.g. `file://`, `gopher://`, `ftp://`) which can lead to file disclosure.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Use timeouts on outbound HTTP requests to prevent attackers from causing denial-of-service by submitting targets that delay responses.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
