---
id: OWASP-A08
title: Software and Data Integrity Failures - Secure Patterns
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
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
### Python - Safe Serialization (JSON)
```python
import json

def load_user_session(cookie_data):
    # SECURE: Parse only primitive data structures using JSON, avoiding code execution risks
    return json.loads(cookie_data)
```

### Java - Safe Jackson JSON Parsing
```java
import com.fasterxml.jackson.databind.ObjectMapper;

public class SessionLoader {
    private ObjectMapper mapper = new ObjectMapper();
    
    public UserSession deserialize(String json) throws Exception {
        // SECURE: Strictly maps input to a typed class structure without executing binary streams
        return mapper.readValue(json, UserSession.class);
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
