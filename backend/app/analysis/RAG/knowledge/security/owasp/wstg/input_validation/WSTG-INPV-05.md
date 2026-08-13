---
knowledge_id: WSTG-WSTG_INPV_05
embedding_title: Testing for SQL Injection - OWASP WSTG WSTG-INPV-05
official_id: WSTG-INPV-05
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
  - inpv
  - cwe-89
keywords:
  - testing for sql injection
  - cwe-89
  - wstg WSTG-INPV-05
aliases:
  - WSTG-WSTG-INPV-05
  - Testing for SQL Injection
related_topics:
  - A03:2021-Injection
  - CWE-89
related_documents:
  - V5.3.1
last_updated: 2026-07-24
---

# Retrieval Summary
OWASP WSTG WSTG-INPV-05 tests for testing for sql injection. This test methodology evaluates applications to ensure detect sql injection vulnerabilities in database access logic across all user input channels. and prevents sql injection enables unauthorized administrative bypass, data exfiltration, and database corruption. across Python web applications.

# Overview
Verify that user-supplied input passed into database operations cannot alter the structure of SQL queries.

# Official Test
Execute OWASP WSTG test WSTG-INPV-05 (Input Validation Testing): Verify that user-supplied input passed into database operations cannot alter the structure of SQL queries.

# Security Objective
Detect SQL injection vulnerabilities in database access logic across all user input channels.

# Why This Matters
SQL Injection enables unauthorized administrative bypass, data exfiltration, and database corruption.

# Threat Model
Attacker supplies `' UNION SELECT username, password_hash FROM users--` in search field to steal credentials.

# Detection Guidance
AI code reviewers should evaluate code paths for un-sanitized call flows using db.session.execute, text(), cursor.execute. Verify whether defense controls prevent unauthorized actions.

# AST Detection Hints
Target AST nodes: `ast.Call (execute, raw), ast.JoinedStr, ast.BinOp (Mod, Add)`.

# Regex / Search Hints
Use regex pattern: `(?i)\.execute\(\s*f['\"].*SELECT` to discover vulnerable candidates.

# Semantic Detection Hints
String interpolation or concatenation used to build SQL query strings.

# Relevant Python APIs
`db.session.execute, text(), cursor.execute`

# Relevant Imports
`from sqlalchemy import text, import sqlite3`

# Vulnerable Patterns
Insecure pattern vulnerable to WSTG WSTG-INPV-05:
```python
def search(term): return db.execute(f"SELECT * FROM users WHERE name LIKE '%{term}%'")
```

# Secure Patterns
Secure implementation satisfying WSTG WSTG-INPV-05:
```python
def search(term): return db.execute(text("SELECT * FROM users WHERE name LIKE :t"), {"t": f"%{term}%"})
```

# Python Example
```python
def search(term): return db.execute(text("SELECT * FROM users WHERE name LIKE :t"), {"t": f"%{term}%"})
```

# FastAPI Example
```python
@app.get('/search')
def search(q: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.username.contains(q)).all()
```

# Flask Example
```python
@app.route('/search')
def search():
    q = request.args.get('q', '')
    return jsonify([u.to_dict() for u in User.query.filter(User.username.like(f'%{q}%')).all()])
```

# Django Example
```python
def search(request):
    q = request.GET.get('q', '')
    return JsonResponse(list(User.objects.filter(username__icontains=q).values()), safe=False)
```

# SQLAlchemy Considerations
session.query(User).filter(User.username == search_term)

# PostgreSQL Considerations
```sql
SELECT * FROM users WHERE username = $1;
```

# Common Developer Mistakes
Attempting to sanitize input by stripping quotes instead of using parameterization.

# False Positives
Using f-strings to format table or column names when validated strictly against an internal static whitelist.

# False Negatives
Using ORM methods like `raw()` or `extra()` with unsanitized string formatting.

# AI Review Heuristics
Flag any dynamic SQL string construction passed directly to execution sinks.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
Scan for DB execution sinks and flag dynamic SQL string construction.

# Review Checklist
- [ ] Execute test procedures for WSTG WSTG-INPV-05.
- [ ] Confirm automated security unit tests cover this scenario.
- [ ] Ensure findings are documented and remediated.

# Remediation
Use parameterized queries or standard ORM abstractions exclusively for all database interactions.

# Related OWASP Top 10
A03:2021-Injection

# Related Cheat Sheets
SQL_Injection_Prevention_Cheat_Sheet

# Related CWE
CWE-89

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
V5.3.1

# References
1. OWASP WSTG Project: https://owasp.org/www-project-web-security-testing-guide/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/89.html
