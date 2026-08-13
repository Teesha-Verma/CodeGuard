---
id: OWASP-A04
title: Insecure Design - Vulnerable Patterns
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
  - design
  - architecture
  - threat-modeling
  - defense-in-depth
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A04_2021-Insecure_Design/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-269
  - CWE-601
  - CWE-657
  - CWE-1173
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Insecure Password Reset Logic
```python
def reset_password(username, security_answer):
    # VULNERABLE: Lacks rate limiting and account lockout. Answers are easily brute-forced.
    user = db.get_user(username)
    if user.answer == security_answer:
        return generate_reset_token(user)
    return "Incorrect answer"
```

### Java - Hardcoded Privilege Mapping
```java
public boolean checkAccess(String role, String resource) {
    // VULNERABLE: Dynamic hardcoded map that is difficult to maintain and audit
    if (role.equals("ADMIN")) return true;
    if (resource.startsWith("/public")) return true;
    return false;
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
