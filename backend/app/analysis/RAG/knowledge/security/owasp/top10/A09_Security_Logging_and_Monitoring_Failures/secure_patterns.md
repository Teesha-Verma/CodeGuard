---
id: OWASP-A09
title: Security Logging and Monitoring Failures - Secure Patterns
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
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
### Python - Safe Structured Logging
```python
import logging
import json

def process_login(username):
    # SECURE: Sanitize input by replacing line breaks, or structure as JSON to prevent forging
    sanitized_user = username.replace('\n', '').replace('\r', '')
    log_payload = {"event": "login_attempt", "user": sanitized_user}
    logging.info(json.dumps(log_payload))
```

### Java - Structured Audit Logging
```java
private static final Logger logger = LoggerFactory.getLogger(LoginController.class);

public boolean loginUser(String user, String pass, String clientIp) {
    boolean authenticated = authService.check(user, pass);
    if (!authenticated) {
        // SECURE: Log failed authentication with context details (excluding credentials)
        logger.warn("SECURITY: Failed login attempt for user={}, ip={}", user, clientIp);
        return false;
    }
    return true;
}
```

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
