---
id: OWASP-A05
title: Security Misconfiguration - Secure Patterns
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
  - misconfiguration
  - hardening
  - headers
  - defaults
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-2
  - CWE-16
  - CWE-200
  - CWE-611
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
### Python - Production Flask Configuration
```python
import os

# SECURE: Read environment type and disable debug mode in production
ENV = os.environ.get("APP_ENV", "production")
DEBUG_MODE = ENV == "development"

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, host='127.0.0.1')
```

### Java - Secure Spring Boot Error Controller
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleAllExceptions(Exception ex) {
        // SECURE: Log internal stack trace locally, return generic message to client
        logger.error("Exception occurred: ", ex);
        Map<String, String> body = new HashMap<>();
        body.put("error", "An internal error occurred. Please contact support.");
        return new ResponseEntity<>(body, HttpStatus.INTERNAL_SERVER_ERROR);
    }
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
