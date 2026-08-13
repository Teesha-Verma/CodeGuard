---
id: OWASP-A10
title: Server-Side Request Forgery - Secure Patterns
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
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
### Python - Strict URL Allowlist
```python
from urllib.parse import urlparse
import requests

ALLOWED_DOMAINS = ["trusted-domain.com", "images.trusted.com"]

@app.route('/fetch-image')
def fetch_image():
    url = request.args.get('url')
    parsed_url = urlparse(url)
    # SECURE: Restrict scheme to HTTPS and restrict domain name to allowlist
    if parsed_url.scheme != 'https' or parsed_url.netloc not in ALLOWED_DOMAINS:
        return "Invalid URL", 400
    r = requests.get(url)
    return r.content
```

### Java - Safe Socket Verification
```java
public void retrieveData(String targetUrl) throws Exception {
    URL url = new URL(targetUrl);
    String host = url.getHost();
    // SECURE: Resolve DNS and check against local subnet ranges
    InetAddress address = InetAddress.getByName(host);
    if (address.isLoopbackAddress() || address.isSiteLocalAddress()) {
        throw new IllegalArgumentException("Requests to internal IP ranges are forbidden");
    }
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    // proceed...
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
