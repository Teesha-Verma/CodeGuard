---
id: OWASP-A07
title: Identification and Authentication Failures - Vulnerable Patterns
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
  - authentication
  - passwords
  - session-management
  - mfa
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-287
  - CWE-307
  - CWE-340
  - CWE-384
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Simple Auth & Insecure Session ID
```python
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # VULNERABLE: Direct match without hashing (A02) and no login rate limit
    user = db.get_user(username)
    if user.password == password:
        # VULNERABLE: Reusable session cookie with no secure attributes
        resp = make_response(redirect('/dashboard'))
        resp.set_cookie('session_id', user.username)
        return resp
```

### Java - Session Fixation Vulnerability
```java
public void authenticateUser(HttpServletRequest request, String username) {
    // VULNERABLE: Authenticating user without regenerating session ID, allowing session fixation
    HttpSession session = request.getSession(false);
    if (session != null) {
        session.setAttribute("user", username);
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
