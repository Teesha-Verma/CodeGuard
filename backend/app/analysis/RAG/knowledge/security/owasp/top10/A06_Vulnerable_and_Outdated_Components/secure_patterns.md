---
id: OWASP-A06
title: Vulnerable and Outdated Components - Secure Patterns
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
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
### Python - Pinned Dependencies with Hashes
```text
# SECURE: Version pinned and verified with cryptographic hashes
requests==2.31.0 --hash=sha256:58cd2187c3e888b5e9e037f6913551d34e56d405b8e97a78e7f1e7d801646253
fastapi==0.100.0 --hash=sha256:0d2a8a816c729fca1a868bb27d49ee417c80521e42845344ad1401f8d48508eb
```

### Java - Upgraded Log4j Dependency
```xml
<!-- SECURE: Upgraded to safe, patched version -->
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.17.1</version>
</dependency>
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
