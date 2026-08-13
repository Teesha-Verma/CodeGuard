---
id: OWASP-A06
title: Vulnerable and Outdated Components - Overview
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: high
priority: medium
tags:
  - dependencies
  - sca
  - patches
  - vulnerable-libraries
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-937
  - CWE-1035
  - CWE-1104
---

# Overview
This vulnerability involves using third-party components (libraries, packages, dependencies, OS packages) that contain known security issues (CVEs). It arises from a lack of dependency inventories and outdated patching workflows.

# Why it matters
Attackers continuously scan for public exploits of third-party libraries (e.g., Log4Shell, Apache Struts exploits). Relying on an outdated component allows attackers to run unauthorized commands, steal information, or compromise backend hosts.

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
ASVS V14.2 (Dependency Management), NIST SP 800-161 (Supply Chain Risk Management).

# References
1. OWASP Top 10 A06: https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
2. OWASP Vulnerable Component Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Vulnerable_and_Outdated_Components_Cheat_Sheet.html
