---
id: OWASP-C6
title: Keep your Components Secure
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
  - keep-your-components-secure
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-937, OWASP A06
---

# Overview
Maintain an inventory of libraries and check for patches to keep third-party components safe.

# Why it matters
Insecure dependencies allow attackers to bypass software defenses using public exploits.

# Detection Rules
Run dependency scanners to map components against CVE listings.

# Bad Code Patterns
```text
# VULNERABLE: Using unpinned dependencies
flask
```

# Good Code Patterns
```text
# SECURE: Pinned and hashed dependency configuration
flask==3.0.0 --hash=sha256:...
```

# Common Mistakes
Allowing libraries without checking vulnerability alerts.

# Secure Alternatives
Adopt automated patch mechanisms and Dependency Track tools.

# Framework Notes
Use locks (poetry.lock, package-lock.json).

# Performance Considerations
Removing unused modules reduces memory consumption and application startup time.

# Related Standards
CWE-937, OWASP A06

# References
OWASP Proactive Controls C6
