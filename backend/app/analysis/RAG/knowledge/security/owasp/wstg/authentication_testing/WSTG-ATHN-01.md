---
knowledge_id: WSTG-WSTG_ATHN_01
embedding_title: Testing for Credentials Transported over Encrypted Channels - OWASP WSTG WSTG-ATHN-01
official_id: WSTG-ATHN-01
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
severity: critical
category: security
subcategory: owasp_wstg
source: OWASP Web Security Testing Guide v4.2
canonical_url: https://owasp.org/www-project-web-security-testing-guide/
tags:
  - wstg
  - athn
  - cwe-319
keywords:
  - testing for credentials transported over encrypted channels
  - cwe-319
  - wstg WSTG-ATHN-01
aliases:
  - WSTG-WSTG-ATHN-01
  - Testing for Credentials Transported over Encrypted Channels
related_topics:
  - A02:2021-Cryptographic Failures
  - CWE-319
related_documents:
  - V9.1.1
last_updated: 2026-07-24
---

# Retrieval Summary
OWASP WSTG WSTG-ATHN-01 tests for testing for credentials transported over encrypted channels. This test methodology evaluates applications to ensure identify unencrypted http authentication endpoints and cleartext credential transmission. and prevents unencrypted http transmissions allow attackers on local networks to sniff credentials and session tokens. across Python web applications.

# Overview
Verify that all authentication requests and sensitive credentials are submitted exclusively over HTTPS/TLS encrypted channels.

# Official Test
Execute OWASP WSTG test WSTG-ATHN-01 (Authentication Testing): Verify that all authentication requests and sensitive credentials are submitted exclusively over HTTPS/TLS encrypted channels.

# Security Objective
Identify unencrypted HTTP authentication endpoints and cleartext credential transmission.

# Why This Matters
Unencrypted HTTP transmissions allow attackers on local networks to sniff credentials and session tokens.

# Threat Model
Attacker performs ARP spoofing or Wi-Fi eavesdropping to intercept cleartext POST request containing username and password.

# Detection Guidance
AI code reviewers should evaluate code paths for un-sanitized call flows using ssl.wrap_socket, HTTPSRedirectMiddleware. Verify whether defense controls prevent unauthorized actions.

# AST Detection Hints
Target AST nodes: `ast.Call (redirect, set_cookie), ast.Assign (SERVER_SSL, HTTP_PORT)`.

# Regex / Search Hints
Use regex pattern: `(?i)(http://|allow_insecure|SSL=False)` to discover vulnerable candidates.

# Semantic Detection Hints
Configuration or route definitions allowing non-TLS connections for authentication endpoints.

# Relevant Python APIs
`ssl.wrap_socket, HTTPSRedirectMiddleware`

# Relevant Imports
`from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware`

# Vulnerable Patterns
Insecure pattern vulnerable to WSTG WSTG-ATHN-01:
```python
app.run(host='0.0.0.0', port=80)
```

# Secure Patterns
Secure implementation satisfying WSTG WSTG-ATHN-01:
```python
app.add_middleware(HTTPSRedirectMiddleware)
```

# Python Example
```python
app.add_middleware(HTTPSRedirectMiddleware)
```

# FastAPI Example
```python
app.add_middleware(HTTPSRedirectMiddleware)
```

# Flask Example
```python
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

# Django Example
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
```

# SQLAlchemy Considerations
engine = create_engine('postgresql://user:pass@db:5432/app?sslmode=require')

# PostgreSQL Considerations
```sql
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
```

# Common Developer Mistakes
Relying on client-side JavaScript to encrypt passwords prior to sending them over HTTP.

# False Positives
Internal microservices running within an encrypted service mesh (e.g. Istio mTLS).

# False Negatives
Redirection from HTTP to HTTPS occurring after credential POST body has already been submitted in cleartext.

# AI Review Heuristics
Flag any web server setup missing HTTPS redirection or HSTS headers on auth routes.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
Inspect web server routing and middleware configuration for HSTS headers and SSL redirect enforcement.

# Review Checklist
- [ ] Execute test procedures for WSTG WSTG-ATHN-01.
- [ ] Confirm automated security unit tests cover this scenario.
- [ ] Ensure findings are documented and remediated.

# Remediation
Enforce HTTP-to-HTTPS redirect middleware, apply HSTS headers, and configure TLS 1.2+ certificates.

# Related OWASP Top 10
A02:2021-Cryptographic Failures

# Related Cheat Sheets
Transport_Layer_Security_Cheat_Sheet

# Related CWE
CWE-319

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
V9.1.1

# References
1. OWASP WSTG Project: https://owasp.org/www-project-web-security-testing-guide/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/319.html
