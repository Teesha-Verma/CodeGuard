---
id: OWASP-API10
title: Unsafe Consumption of APIs
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
  - api-security
  - unsafe-consumption-of-apis
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-20, OWASP Top 10 A08
---

# Overview
Unsafe Consumption of APIs happens when an application trusts data returned from third-party APIs without proper validation.

# Why it matters
If the third-party API is compromised, the host application will process malicious inputs, leading to SQLi, XSS, or RCE.

# Detection Rules
Audit external API client connections and trace incoming data objects through security validation layers.

# Bad Code Patterns
```python
# VULNERABLE: Direct database insert of third-party API response data
def sync_weather():
    data = requests.get('https://api.weather.com/data').json()
    db.execute(f"INSERT INTO status VALUES ('{data['status']}')")
```

# Good Code Patterns
```python
# SECURE: Validate data format and use parameterized queries
def sync_weather():
    data = requests.get('https://api.weather.com/data').json()
    status_val = str(data.get('status', 'Unknown'))
    # Use parameterized database write
    db.execute("INSERT INTO status VALUES (:status)", {"status": status_val})
```

# Common Mistakes
Assuming data from trusted partners does not require filtering or sanitization.

# Secure Alternatives
Treat all third-party API payloads as untrusted input. Validate format, length, and content.

# Framework Notes
Use deserialization models (like Pydantic) to strictly check external API payloads.

# Performance Considerations
Isolate external API client threads to avoid third-party network delays blocking the rest of the application.

# Related Standards
CWE-20, OWASP Top 10 A08

# References
OWASP API Security Top 10: API10:2023
