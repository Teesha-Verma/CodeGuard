---
id: OWASP-A02
title: Cryptographic Failures - Vulnerable Patterns
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
### Python - Insecure MD5 Hashing & Hardcoded Key
```python
import hashlib

def hash_password(password):
    # VULNERABLE: MD5 is broken and easily cracked
    return hashlib.md5(password.encode()).hexdigest()

SECRET_KEY = "super_secret_key_12345" # VULNERABLE: Hardcoded secret
```

### Java - Insecure Randomness
```java
import java.util.Random;

public class InsecureKeyGenerator {
    public int generateToken() {
        // VULNERABLE: Insecure pseudo-random number generator
        Random r = new Random();
        return r.nextInt();
    }
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
