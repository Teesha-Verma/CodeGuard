---
id: OWASP-A02
title: Cryptographic Failures - Secure Patterns
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
  - cryptography
  - encryption
  - hashing
  - sensitive-data
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-311
  - CWE-327
  - CWE-328
  - CWE-757
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
### Python - Secure Argon2 Hashing & Environment Config
```python
from argon2 import PasswordHasher
import os

ph = PasswordHasher()

def hash_password(password):
    # SECURE: Argon2 is a robust password hashing algorithm
    return ph.hash(password)

# SECURE: Read key from environment variable
SECRET_KEY = os.environ.get("APP_SECRET_KEY")
```

### Java - Secure Cryptographic Randomness
```java
import java.security.SecureRandom;

public class SecureKeyGenerator {
    public int generateToken() {
        // SECURE: Cryptographically strong random number generator
        SecureRandom sr = new SecureRandom();
        return sr.nextInt();
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
