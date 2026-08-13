---
id: OWASP-A06
title: Vulnerable and Outdated Components - Vulnerable Patterns
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: high
priority: medium
tags:
  - dependencies
  - sca
  - patches
  - vulnerable-libraries
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-937
  - CWE-1035
  - CWE-1104
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Unlocked Dependencies in requirements.txt
```text
# VULNERABLE: No version pinning. Builds can pull highly outdated, insecure dependencies.
requests
fastapi
sqlalchemy
```

### Java - Insecure Log4j Dependency
```xml
<!-- VULNERABLE: Using version with Log4Shell (CVE-2021-44228) -->
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.14.1</version>
</dependency>
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
