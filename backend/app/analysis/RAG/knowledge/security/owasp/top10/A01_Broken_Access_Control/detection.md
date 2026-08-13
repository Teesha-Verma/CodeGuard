---
id: OWASP-A01
title: Broken Access Control - Detection
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: critical
priority: high
tags:
  - access-control
  - authorization
  - idor
  - privilege-escalation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A01_2021-Broken_Access_Control/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-22
  - CWE-284
  - CWE-285
  - CWE-639
---

# Overview
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Verify all endpoints enforce authorization checks based on user identity and roles.
2. Review routing and middleware configurations to ensure access policies are applied globally.
3. Perform manual testing for Indirect Object References (IDOR) by modifying parameters (e.g. user_id, doc_id).
4. Run automated DAST tools to scan for endpoints accessible without authentication.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Relying on client-side routing or UI hiding to enforce permissions (e.g., hiding a delete button in the UI without protecting the backend API endpoint).
2. Hardcoding role names inside controllers rather than leveraging authorization policies or middlewares.
3. Using sequential IDs instead of UUIDs, making it trivial for attackers to discover and harvest records via IDOR.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Caching user permissions in memory (e.g., Redis) can significantly reduce database lookup overhead for access control checks. Ensure cache invalidation policies are robust.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
