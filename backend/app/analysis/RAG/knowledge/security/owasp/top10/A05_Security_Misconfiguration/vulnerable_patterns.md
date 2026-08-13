---
id: OWASP-A05
title: Security Misconfiguration - Vulnerable Patterns
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
### Python - Flask Debug Mode Enabled
```python
if __name__ == '__main__':
    # VULNERABLE: Running Flask in debug mode in production exposes an interactive debugger console
    app.run(debug=True, host='0.0.0.0')
```

### Java - Raw Error Page Exposure
```xml
<!-- VULNERABLE: web.xml allowing system stack traces to display on errors -->
<error-page>
    <exception-type>java.lang.Throwable</exception-type>
    <location>/error.jsp</location> <!-- If error.jsp prints exception.printStackTrace() -->
</error-page>
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
