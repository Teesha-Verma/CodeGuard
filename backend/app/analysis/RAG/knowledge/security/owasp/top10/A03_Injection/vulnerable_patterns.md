---
id: OWASP-A03
title: Injection - Vulnerable Patterns
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: critical
priority: high
tags:
  - injection
  - sqli
  - command-injection
  - input-validation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A03_2021-Injection/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-78
  - CWE-89
  - CWE-94
  - CWE-562
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Raw SQL Concatenation
```python
def get_user_data(username):
    # VULNERABLE: Direct SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
```

### Java - Raw Process Exec
```java
public void executePing(String ip) throws IOException {
    // VULNERABLE: OS command injection
    Runtime.getRuntime().exec("ping -c 3 " + ip);
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
