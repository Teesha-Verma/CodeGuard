---
id: OWASP-C9
title: Implement Security Logging and Monitoring
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
  - implement-security-logging-and-monitoring
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-778, OWASP A09
---

# Overview
Log security-critical operations in a structured format and monitor them to identify breaches.

# Why it matters
Inadequate monitoring keeps intrusions hidden, blocking investigations and incident containment.

# Detection Rules
Confirm failed login attempts and permission actions write entries to logs. Check for sensitive data.

# Bad Code Patterns
```python
# VULNERABLE: Logging sensitive customer password data
logger.info(f"User {username} logged in with pass {password}")
```

# Good Code Patterns
```python
# SECURE: Structured JSON logs containing only metadata
logger.info(json.dumps({"event": "auth_success", "user": username, "ip": client_ip}))
```

# Common Mistakes
Writing logs to local files without shipping them to centralized storage.

# Secure Alternatives
Deploy SIEM tools and structured JSON log pipelines.

# Framework Notes
Utilize logging configuration libraries (Logback, python-logging).

# Performance Considerations
Set logging activities to execute asynchronously to prevent locking main request threads.

# Related Standards
CWE-778, OWASP A09

# References
OWASP Proactive Controls C9
