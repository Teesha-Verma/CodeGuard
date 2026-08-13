---
id: OWASP-A10
title: Server-Side Request Forgery - Vulnerable Patterns
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
  - ssrf
  - network-security
  - url-validation
  - allowlist
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-918
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Arbitrary URL Fetch
```python
import requests

@app.route('/fetch-image')
def fetch_image():
    url = request.args.get('url')
    # VULNERABLE: Directly fetching user-supplied URL allows SSRF
    r = requests.get(url)
    return r.content
```

### Java - Raw HTTP Connection
```java
public void retrieveData(String targetUrl) throws Exception {
    // VULNERABLE: Direct connection to arbitrary user input URL
    URL url = new URL(targetUrl);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    conn.setRequestMethod("GET");
    conn.getInputStream().read();
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
