---
id: OWASP-A03
title: Injection - Detection
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
  - injection
  - sqli
  - command-injection
  - input-validation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A03_2021-Injection/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-78
  - CWE-89
  - CWE-94
  - CWE-562
---

# Overview
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
1. Identify all instances of dynamic SQL statements constructed via string formatting or concatenation.
2. Use SAST tools to trace user input from endpoints (sources) to database execution or shell invocation (sinks).
3. Test for SQLi using automated tools (e.g. sqlmap) or manual payload injection.
4. Review input validation layers and parameterized query configurations.

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
1. Attempting to sanitize input by blacklisting certain characters (e.g., removing `'` or `;`), which is bypassable.
2. Using ORMs but executing raw queries using string concatenation inside the ORM context.
3. Relying on database triggers or stored procedures to prevent SQL injection without checking parameterization.

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
Parameterized queries enable database engines to reuse execution plans, reducing CPU overhead and memory footprint on the database server.

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
