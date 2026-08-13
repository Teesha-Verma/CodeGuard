---
knowledge_id: WSTG-WSTG_INPV_19
embedding_title: Testing for Server-Side Request Forgery (SSRF) - OWASP WSTG WSTG-INPV-19
official_id: WSTG-INPV-19
document_type: wstg_test
chunk_type: concept_and_detection
language:
  - python
frameworks:
  - fastapi
  - flask
  - django
database:
  - sqlalchemy
  - postgresql
retrieval_priority: high
source_version: 4.2
confidence: official
severity: high
category: security
subcategory: owasp_wstg
source: OWASP Web Security Testing Guide v4.2
canonical_url: https://owasp.org/www-project-web-security-testing-guide/
tags:
  - wstg
  - inpv
  - cwe-918
keywords:
  - testing for server-side request forgery (ssrf)
  - cwe-918
  - wstg WSTG-INPV-19
aliases:
  - WSTG-WSTG-INPV-19
  - Testing for Server-Side Request Forgery (SSRF)
related_topics:
  - A10:2021-Server-Side Request Forgery
  - CWE-918
related_documents:
  - V12.6.1
last_updated: 2026-07-24
---

# Retrieval Summary
OWASP WSTG WSTG-INPV-19 tests for testing for server-side request forgery (ssrf). This test methodology evaluates applications to ensure identify endpoints where server fetches user-controlled urls without resolving ip ranges or restricting internal subnets. and prevents ssrf enables attackers to scan internal networks, query local services, and access cloud metadata apis. across Python web applications.

# Overview
Verify that user-supplied URLs or network targets fetched by the server are restricted to validated allowlists.

# Official Test
Execute OWASP WSTG test WSTG-INPV-19 (Input Validation Testing): Verify that user-supplied URLs or network targets fetched by the server are restricted to validated allowlists.

# Security Objective
Identify endpoints where server fetches user-controlled URLs without resolving IP ranges or restricting internal subnets.

# Why This Matters
SSRF enables attackers to scan internal networks, query local services, and access cloud metadata APIs.

# Threat Model
Attacker submits `http://169.254.169.254/latest/meta-data/` to steal AWS IAM credentials.

# Detection Guidance
AI code reviewers should evaluate code paths for un-sanitized call flows using requests.get, httpx.AsyncClient, urllib.request.urlopen. Verify whether defense controls prevent unauthorized actions.

# AST Detection Hints
Target AST nodes: `ast.Call (requests.get, urllib.request.urlopen, httpx.get)`.

# Regex / Search Hints
Use regex pattern: `(?i)(requests|httpx|urllib)\.(get|post|request)\(\s*\w+` to discover vulnerable candidates.

# Semantic Detection Hints
Passing user-controlled URL string directly to outbound HTTP clients without hostname allowlisting.

# Relevant Python APIs
`requests.get, httpx.AsyncClient, urllib.request.urlopen`

# Relevant Imports
`import requests, import httpx, from urllib.parse import urlparse`

# Vulnerable Patterns
Insecure pattern vulnerable to WSTG WSTG-INPV-19:
```python
@app.post('/fetch')
def fetch_url(url: str): return requests.get(url).content
```

# Secure Patterns
Secure implementation satisfying WSTG WSTG-INPV-19:
```python
ALLOWED = {'cdn.example.com'}
def fetch_url(url: str):
    p = urlparse(url)
    if p.scheme != 'https' or p.netloc not in ALLOWED: raise ValueError('Denied')
    return requests.get(url, timeout=5).content
```

# Python Example
```python
ALLOWED = {'cdn.example.com'}
def fetch_url(url: str):
    p = urlparse(url)
    if p.scheme != 'https' or p.netloc not in ALLOWED: raise ValueError('Denied')
    return requests.get(url, timeout=5).content
```

# FastAPI Example
```python
@app.post('/webhook')
def reg_webhook(url: HttpUrl):
    p = urlparse(str(url))
    if p.hostname in ('localhost', '127.0.0.1', '169.254.169.254'): raise HTTPException(400)
    return {'status': 'ok'}
```

# Flask Example
```python
@app.route('/fetch')
def fetch():
    u = request.args.get('url')
    if urlparse(u).netloc not in ALLOWED: abort(400)
    return requests.get(u, timeout=3).content
```

# Django Example
```python
def fetch(request):
    u = request.GET.get('url')
    if not is_safe_url(u): return HttpResponseBadRequest()
    return HttpResponse(requests.get(u).content)
```

# SQLAlchemy Considerations
# Store approved webhook domain configurations in database table

# PostgreSQL Considerations
```sql
-- Maintain allowlist of remote webhooks in PostgreSQL lookup table
```

# Common Developer Mistakes
Blacklisting `localhost` while failing to block IPv6 `::1` or decimal IP notation `2130706433`.

# False Positives
Outbound API calls to hardcoded static third-party integrations (e.g. Stripe API).

# False Negatives
Validating hostname but following HTTP 302 redirects to internal IP addresses.

# AI Review Heuristics
Flag any outbound HTTP request using a variable URL parameter without domain validation.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
Locate outbound HTTP client calls and check for domain allowlist and DNS resolution checks.

# Review Checklist
- [ ] Execute test procedures for WSTG WSTG-INPV-19.
- [ ] Confirm automated security unit tests cover this scenario.
- [ ] Ensure findings are documented and remediated.

# Remediation
Enforce strict domain allowlists, resolve DNS to verify IPs are not in private ranges, and disable HTTP redirects.

# Related OWASP Top 10
A10:2021-Server-Side Request Forgery

# Related Cheat Sheets
Server_Side_Request_Forgery_Prevention_Cheat_Sheet

# Related CWE
CWE-918

# Related CERT Python Rules
IDS01-P. Normalize strings before validating them.

# Related PEPs
PEP 8 -- Style Guide for Python Code

# Related Security Patterns
Input Validation, Sanitization, Least Privilege.

# Related Anti-Patterns
Bypassing Controls, Insufficient Logging, Trusting Client State.

# Related Repository Rules
Rule-SEC-02: Ensure all input interfaces and authentication endpoints pass security verification.

# Related ASVS Requirements
V12.6.1

# References
1. OWASP WSTG Project: https://owasp.org/www-project-web-security-testing-guide/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/918.html
