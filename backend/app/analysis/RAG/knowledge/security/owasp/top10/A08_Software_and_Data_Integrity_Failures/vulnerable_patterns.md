---
id: OWASP-A08
title: Software and Data Integrity Failures - Vulnerable Patterns
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
  - integrity
  - deserialization
  - ci-cd
  - signatures
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-502
  - CWE-494
  - CWE-829
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Insecure Deserialization (pickle)
```python
import pickle

def load_user_session(cookie_data):
    # VULNERABLE: Direct deserialization of user-provided data allows arbitrary code execution
    return pickle.loads(cookie_data)
```

### Java - Insecure Deserialization
```java
import java.io.ObjectInputStream;
import java.io.InputStream;

public class SessionLoader {
    public Object deserialize(InputStream is) throws Exception {
        // VULNERABLE: Restoring objects from untrusted streams allows RCE
        ObjectInputStream ois = new ObjectInputStream(is);
        return ois.readObject();
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
