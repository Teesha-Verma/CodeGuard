---
id: OWASP-A10
title: Server-Side Request Forgery - Overview
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
Server-Side Request Forgery (SSRF) occurs when a web application fetches a remote resource from a user-supplied URL without validating the address. This allows attackers to force the server to send HTTP/TCP requests to internal resources, metadata endpoints, or third-party APIs.

# Why it matters
SSRF can be leveraged to scan internal private ports, bypass firewall controls, and access cloud metadata services (e.g., AWS IMDSv1/v2 at `169.254.169.254`), exposing IAM keys and database credentials.

# Detection Rules
*Refer to [detection.md](detection.md) for details on detecting this vulnerability.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
ASVS V5.2 (Sanitization and Input Validation), NIST SP 800-53 SC-7 (Boundary Protection).

# References
1. OWASP Top 10 A10: https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/
2. OWASP SSRF Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
