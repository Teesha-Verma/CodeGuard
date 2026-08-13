---
knowledge_id: KB-IDS01_P
embedding_title: Do not pass unsanitized user input to system commands - Security Knowledge Document
official_id: IDS01-P
document_type: cert_python
chunk_type: concept_and_detection
title: Do not pass unsanitized user input to system commands
category: security
subcategory: cert_python
version: 1.0.0
source: Official Security Documentation
canonical_url: https://cwe.mitre.org/
source_version: 2026.1
language: python
frameworks:
  - fastapi
  - flask
  - django
database:
  - sqlalchemy
  - postgresql
severity: high
retrieval_priority: high
confidence: official
tags:
  - security
  - cert_python
  - cwe-78
keywords:
  - do not pass unsanitized user input to system commands
  - cwe-78
aliases:
  - IDS01-P
  - Do not pass unsanitized user input to system commands
related_topics:
  - A03:2021-Injection
  - CWE-78
related_documents:
  - V1.1.1
  - WSTG-INFO-10
last_updated: 2026-07-24
---

# Retrieval Summary
This document covers Do not pass unsanitized user input to system commands (IDS01-P). It defines security objectives, threat models, detection guidance, AST hints, and Python code examples across FastAPI, Flask, and Django to eliminate vulnerabilities and ensure robust software assurance.

# Overview
Passing untrusted input directly to shell processes allows execution of arbitrary commands.

# Official Definition
Official standard requirement enforcing security controls and secure coding practices.

# Security Objective
Mitigate security risks and prevent unauthorized exploitation in application logic.

# Why This Matters
Unmitigated vulnerabilities lead to privilege escalation, data breaches, and service disruption.

# Threat Model
Attacker submits malicious payload targeting un-sanitized application components.

# Detection Guidance
AI code reviewers should scan Python source files for unvalidated usage of os.system, subprocess.run. Look for missing authorization checks or un-parameterized dynamic input.

# AST Detection Hints
Target AST nodes: `ast.Call, ast.Import, ast.FunctionDef`.

# Regex Detection Hints
Use regex pattern: `(?i)(eval|exec|os\.system|subprocess|input)` to flag candidate vulnerabilities.

# Semantic Detection Hints
Unsanitized user input flowing directly into system execution or database sinks.

# Relevant Python APIs
`os.system, subprocess.run`

# Relevant Imports
`import os, import subprocess`

# Vulnerable Patterns
Insecure implementation:
```python
os.system('cat ' + filename)
```

# Secure Patterns
Secure implementation:
```python
subprocess.run(['cat', filename], check=True)
```

# Python Example
```python
subprocess.run(['cat', filename], check=True)
```

# FastAPI Example
```python
@app.post('/process')
def process(data: str = Body(...)):
    if not data.isalnum(): raise HTTPException(400, 'Invalid')
    return {'status': 'success'}
```

# Flask Example
```python
@app.route('/process', methods=['POST'])
def process():
    data = request.json.get('data', '')
    if not data.isalnum(): abort(400)
    return jsonify({'status': 'success'})
```

# Django Example
```python
def process(request):
    data = request.POST.get('data', '')
    if not data.isalnum(): return HttpResponseBadRequest()
    return JsonResponse({'status': 'success'})
```

# SQLAlchemy Considerations
# Enforce model attribute validation before database commit

# PostgreSQL Considerations
```sql
-- Use domain constraints and check rules on table columns
```

# Common Developer Mistakes
Relying strictly on client-side validation without server-side enforcement.

# False Positives
Internal administrative management scripts executed within trusted execution boundaries.

# False Negatives
Validating parameter type but failing to sanitize payload content values.

# AI Review Heuristics
Flag unvalidated input parameters passed directly into execution sinks.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
1. Trace input parameters to sink functions. 2. Verify validation guards. 3. Flag missing checks.

# Review Checklist
- [ ] Verify requirement for IDS01-P is enforced in code.
- [ ] Confirm automated security unit tests cover this rule.
- [ ] Ensure secure default fallback if validation fails.

# Remediation
Implement server-side input validation, strict type constraints, and secure parameterization.

# Related OWASP Top 10
A03:2021-Injection

# Related ASVS Requirements
V1.1.1

# Related WSTG Tests
WSTG-INFO-10

# Related CWE
CWE-78

# Related CERT Python Rules
IDS01-P

# Related NIST Guidance
SP-800-218

# Related Security Patterns
Input_Validation_Pattern

# Related Anti-Patterns
Missing_Input_Validation

# Related Repository Rules
Rule-SEC-01: Enforce security validation and access control on all endpoints.

# Related PEPs
PEP 8 -- Style Guide for Python Code

# References
1. Official Security Standard: https://cwe.mitre.org/data/definitions/78.html
