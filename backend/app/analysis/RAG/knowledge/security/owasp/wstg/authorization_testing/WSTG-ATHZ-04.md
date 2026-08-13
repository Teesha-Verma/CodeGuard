---
knowledge_id: WSTG-WSTG_ATHZ_04
embedding_title: Testing for Insecure Direct Object References (IDOR) - OWASP WSTG WSTG-ATHZ-04
official_id: WSTG-ATHZ-04
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
  - athz
  - cwe-639
keywords:
  - testing for insecure direct object references (idor)
  - cwe-639
  - wstg WSTG-ATHZ-04
aliases:
  - WSTG-WSTG-ATHZ-04
  - Testing for Insecure Direct Object References (IDOR)
related_topics:
  - A01:2021-Broken Access Control
  - CWE-639
related_documents:
  - V4.2.1
last_updated: 2026-07-24
---

# Retrieval Summary
OWASP WSTG WSTG-ATHZ-04 tests for testing for insecure direct object references (idor). This test methodology evaluates applications to ensure identify endpoints where changing record identifiers returns records belonging to other users. and prevents idor allows attackers to harvest or modify all records in a database by enumerating sequential ids. across Python web applications.

# Overview
Verify that user-supplied object keys cannot be manipulated to access unauthorized resources.

# Official Test
Execute OWASP WSTG test WSTG-ATHZ-04 (Authorization Testing): Verify that user-supplied object keys cannot be manipulated to access unauthorized resources.

# Security Objective
Identify endpoints where changing record identifiers returns records belonging to other users.

# Why This Matters
IDOR allows attackers to harvest or modify all records in a database by enumerating sequential IDs.

# Threat Model
Attacker changes URL `/api/user/101/invoice` to `/api/user/102/invoice` to view another user's invoice.

# Detection Guidance
AI code reviewers should evaluate code paths for un-sanitized call flows using db.session.query, filter, get_object_or_404. Verify whether defense controls prevent unauthorized actions.

# AST Detection Hints
Target AST nodes: `ast.FunctionDef, ast.Call (filter, get, query)`.

# Regex / Search Hints
Use regex pattern: `(?i)filter_by\(id\s*=\s*\w+\)(?!\.filter\(.*user_id)` to discover vulnerable candidates.

# Semantic Detection Hints
Fetching records using user-supplied ID parameters without scoping the query to active user ID.

# Relevant Python APIs
`db.session.query, filter, get_object_or_404`

# Relevant Imports
`from django.shortcuts import get_object_or_404`

# Vulnerable Patterns
Insecure pattern vulnerable to WSTG WSTG-ATHZ-04:
```python
@app.get('/invoice/{id}')
def get_invoice(id: int): return db.query(Invoice).get(id)
```

# Secure Patterns
Secure implementation satisfying WSTG WSTG-ATHZ-04:
```python
@app.get('/invoice/{id}')
def get_invoice(id: int, user=Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == id, Invoice.user_id == user.id).first()
    if not inv: raise HTTPException(404)
    return inv
```

# Python Example
```python
@app.get('/invoice/{id}')
def get_invoice(id: int, user=Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == id, Invoice.user_id == user.id).first()
    if not inv: raise HTTPException(404)
    return inv
```

# FastAPI Example
```python
@app.get('/doc/{id}')
def read_doc(id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id, Document.user_id == user.id).first()
    if not doc: raise HTTPException(404)
    return doc
```

# Flask Example
```python
@app.route('/doc/<id>')
@login_required
def read_doc(id):
    doc = Document.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return jsonify(doc.to_dict())
```

# Django Example
```python
def read_doc(request, id):
    doc = get_object_or_404(Document, id=id, owner=request.user)
    return JsonResponse({'title': doc.title})
```

# SQLAlchemy Considerations
query = session.query(Order).filter(Order.id == order_id, Order.user_id == current_user_id)

# PostgreSQL Considerations
```sql
CREATE POLICY user_orders_policy ON orders FOR ALL USING (user_id = current_setting('app.current_user_id')::int);
```

# Common Developer Mistakes
Relying on GUID complexity alone without verifying ownership on backend queries.

# False Positives
Endpoints serving public un-restricted resources (e.g. public blog posts).

# False Negatives
Checking permissions on GET requests but forgetting to apply owner filters on PUT/DELETE routes.

# AI Review Heuristics
Flag any route taking an ID parameter where database query does not filter by active user/tenant ID.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
Identify route accepting resource ID, trace database lookup logic, and check for user ownership filter.

# Review Checklist
- [ ] Execute test procedures for WSTG WSTG-ATHZ-04.
- [ ] Confirm automated security unit tests cover this scenario.
- [ ] Ensure findings are documented and remediated.

# Remediation
Scope all database queries to include active user/tenant ownership filters.

# Related OWASP Top 10
A01:2021-Broken Access Control

# Related Cheat Sheets
Authorization_Cheat_Sheet

# Related CWE
CWE-639

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
V4.2.1

# References
1. OWASP WSTG Project: https://owasp.org/www-project-web-security-testing-guide/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/639.html
