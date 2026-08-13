---
id: OWASP-API6
title: Unrestricted Access to Sensitive Business Flows
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
  - unrestricted-access-to-sensitive-business-flows
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - CWE-799, OWASP Top 10 A04
---

# Overview
This vulnerability occurs when APIs expose business logic flows (like account creation, purchasing, booking) without considering automated exploitation or excessive usage.

# Why it matters
Bots can script actions to buy up limited inventory, scrape pricing, or spam account registration systems.

# Detection Rules
1. Check if endpoints lack rate limiting or CAPTCHA validation.
2. Verify system cannot identify automated user agent patterns.

# Bad Code Patterns
```python
# VULNERABLE: Simple submission route with no bot checks
@app.post('/api/ticket/purchase')
def buy_ticket(ticket_id: int):
    return transaction_service.process(ticket_id)
```

# Good Code Patterns
```python
# SECURE: Require CAPTCHA validation token and apply strict ip rate limits
@app.post('/api/ticket/purchase')
@limiter.limit("2 per minute")
def buy_ticket(ticket_id: int, captcha_token: str = Header(...)):
    verify_captcha(captcha_token)
    return transaction_service.process(ticket_id)
```

# Common Mistakes
Assuming simple authorization rules are sufficient to stop bot nets.

# Secure Alternatives
Integrate device fingerprinting, CAPTCHA solutions, and threshold monitors.

# Framework Notes
Configure WAF (Web Application Firewall) policies to detect headless browser fingerprints.

# Performance Considerations
Differentiate static requests from transaction API calls to selectively apply heavy bot defenses.

# Related Standards
CWE-799, OWASP Top 10 A04

# References
OWASP API Security Top 10: API6:2023
