---
id: OWASP-C5
title: Secure By Default Configurations
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
  - secure-by-default-configurations
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-16, OWASP A05
---

# Overview
Deliver applications and systems hardened, requiring explicit configuration changes to decrease security controls.

# Why it matters
Default accounts and loose transport privileges are the easiest entry points for scanners.

# Detection Rules
Scan setup scripts for default passwords, active admin accounts, or debug ports.

# Bad Code Patterns
```python
# VULNERABLE: Default credentials and public database access
DB_PASS = 'postgres'
DB_HOST = '0.0.0.0'
```

# Good Code Patterns
```python
# SECURE: Enforced configuration overrides and localhost limits
DB_PASS = os.environ['DB_PASSWORD']
DB_HOST = '127.0.0.1'
```

# Common Mistakes
Deploying default config files. Leaving sample pages active.

# Secure Alternatives
Enforce hardening policies using automated deployment environments.

# Framework Notes
Configure framework environments to production by default.

# Performance Considerations
Hardening server ports blocks background scan traffic, saving processing threads.

# Related Standards
CWE-16, OWASP A05

# References
OWASP Proactive Controls C5
