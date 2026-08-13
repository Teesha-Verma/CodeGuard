---
id: OWASP-A09
title: Security Logging and Monitoring Failures - Vulnerable Patterns
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
  - logging
  - monitoring
  - audit-logs
  - siem
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-117
  - CWE-778
  - CWE-779
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Log Injection Vulnerability
```python
import logging

def process_login(username):
    # VULNERABLE: Writing unvalidated user input directly into logs (Log Injection/Forging)
    logging.info(f"User {username} attempted login")
```

### Java - Omission of Security Event Logging
```java
public boolean loginUser(String user, String pass) {
    boolean authenticated = authService.check(user, pass);
    if (!authenticated) {
        // VULNERABLE: Failed authentication attempts are not logged, blinding administrators to brute force
        return false;
    }
    return true;
}
```

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for secure patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
