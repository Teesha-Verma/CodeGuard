---
id: OWASP-C4
title: Address Security from the Start
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
  - address-security-from-the-start
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-1173, OWASP A04
---

# Overview
Incorporate security design guidelines, threat modeling, and testing into the early stages of software development lifecycle (SDLC).

# Why it matters
Design defects are extremely expensive to remediate if detected in production.

# Detection Rules
Confirm threat modeling documents are created before coding features. Verify security tests run in CI.

# Bad Code Patterns
```text
# VULNERABLE: Standard design document with zero mention of threat modeling or data privacy controls
```

# Good Code Patterns
```text
# SECURE: Design review includes a STRIDE threat map and security verification requirements
```

# Common Mistakes
Treating security checks as a separate phase before deployment rather than a continuous cycle.

# Secure Alternatives
Adopt SSDLC (Secure Software Development Lifecycle) principles.

# Framework Notes
Use containerized checks and SAST linters inside pipeline scripts.

# Performance Considerations
Shift-left reduces development cycles by catching bugs before deployment.

# Related Standards
CWE-1173, OWASP A04

# References
OWASP Proactive Controls C4
