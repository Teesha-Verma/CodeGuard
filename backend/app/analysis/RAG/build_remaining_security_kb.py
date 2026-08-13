import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge\security"

# Subfolders
CWE_DIR = os.path.join(BASE_DIR, "cwe")
CERT_DIR = os.path.join(BASE_DIR, "cert", "python")
NIST_DIR = os.path.join(BASE_DIR, "nist")
PATTERNS_DIR = os.path.join(BASE_DIR, "security_patterns")
ANTI_PATTERNS_DIR = os.path.join(BASE_DIR, "anti_patterns")

for d in [CWE_DIR, CERT_DIR, NIST_DIR, PATTERNS_DIR, ANTI_PATTERNS_DIR]:
    os.makedirs(d, exist_ok=True)

print("Starting Remaining Security Knowledge Base Builder...")

# Generic Sanitizer
def sanitize(item, doc_type):
    defaults = {
        "severity": "high", "priority": "high", "cwe": "CWE-20",
        "top10": "A04:2021-Insecure Design", "asvs": "V1.1.1", "wstg": "WSTG-INFO-10",
        "cert": "IDS01-P", "nist": "SP-800-218", "pattern": "Input_Validation_Pattern",
        "anti_pattern": "Missing_Input_Validation",
        "overview": "Defines core principles and technical implementation constraints for secure application development.",
        "official_def": "Official standard requirement enforcing security controls and secure coding practices.",
        "objective": "Mitigate security risks and prevent unauthorized exploitation in application logic.",
        "why": "Unmitigated vulnerabilities lead to privilege escalation, data breaches, and service disruption.",
        "threat_model": "Attacker submits malicious payload targeting un-sanitized application components.",
        "ast_hints": "ast.Call, ast.Import, ast.FunctionDef",
        "regex_hints": r"(?i)(eval|exec|os\.system|subprocess|input)",
        "semantic_hints": "Unsanitized user input flowing directly into system execution or database sinks.",
        "apis": "os.system, subprocess.run", "imports": "import os, import subprocess",
        "bad_code": "def process_data(input_data):\n    # VULNERABLE: Direct unsanitized input execution\n    os.system(f'process {input_data}')",
        "good_code": "def process_data(input_data: str):\n    # SECURE: Strict validation\n    if not input_data.isalnum(): raise ValueError('Invalid input')\n    subprocess.run(['/usr/bin/process', input_data], check=True)",
        "fastapi": "@app.post('/process')\ndef process(data: str = Body(...)):\n    if not data.isalnum(): raise HTTPException(400, 'Invalid')\n    return {'status': 'success'}",
        "flask": "@app.route('/process', methods=['POST'])\ndef process():\n    data = request.json.get('data', '')\n    if not data.isalnum(): abort(400)\n    return jsonify({'status': 'success'})",
        "django": "def process(request):\n    data = request.POST.get('data', '')\n    if not data.isalnum(): return HttpResponseBadRequest()\n    return JsonResponse({'status': 'success'})",
        "sqlalchemy": "# Enforce model attribute validation before database commit",
        "postgresql": "-- Use domain constraints and check rules on table columns",
        "mistakes": "Relying strictly on client-side validation without server-side enforcement.",
        "fps": "Internal administrative management scripts executed within trusted execution boundaries.",
        "fns": "Validating parameter type but failing to sanitize payload content values.",
        "heuristics": "Flag unvalidated input parameters passed directly into execution sinks.",
        "confidence": "high", "reasoning": "1. Trace input parameters to sink functions. 2. Verify validation guards. 3. Flag missing checks.",
        "remediation": "Implement server-side input validation, strict type constraints, and secure parameterization."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    return item

# 1. CWE Dataset
CWE_DATASET = [
    {
        "id": "CWE-89", "title": "Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')",
        "overview": "The software constructs an SQL command using externally-influenced input without parameterization.",
        "cwe": "CWE-89", "top10": "A03:2021-Injection", "asvs": "V5.3.1", "wstg": "WSTG-INPV-05",
        "bad_code": "cursor.execute(f\"SELECT * FROM users WHERE name = '{name}'\")",
        "good_code": "cursor.execute(\"SELECT * FROM users WHERE name = %s\", (name,))"
    },
    {
        "id": "CWE-78", "title": "Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')",
        "overview": "The software constructs an OS command using externally-influenced input without proper neutralization.",
        "cwe": "CWE-78", "top10": "A03:2021-Injection", "asvs": "V5.3.1", "wstg": "WSTG-INPV-12",
        "bad_code": "os.system(f'ping -c 1 {user_ip}')",
        "good_code": "subprocess.run(['ping', '-c', '1', user_ip], check=True)"
    },
    {
        "id": "CWE-79", "title": "Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')",
        "overview": "The software does not neutralize or incorrectly neutralizes user-controllable input before rendering it in web pages.",
        "cwe": "CWE-79", "top10": "A03:2021-Injection", "asvs": "V5.2.1", "wstg": "WSTG-INPV-01",
        "bad_code": "return f'<div>Hello {user_input}</div>'",
        "good_code": "return render_template('hello.html', name=user_input)"
    },
    {
        "id": "CWE-502", "title": "Deserialization of Untrusted Data",
        "overview": "The application deserializes untrusted data without verifying that the resulting data is valid or safe.",
        "cwe": "CWE-502", "top10": "A08:2021-Software and Data Integrity Failures", "asvs": "V10.1.1", "wstg": "WSTG-INPV-11",
        "bad_code": "pickle.loads(user_raw_data)",
        "good_code": "json.loads(user_raw_data)"
    },
    {
        "id": "CWE-918", "title": "Server-Side Request Forgery (SSRF)",
        "overview": "The web application fetches a remote resource without validating the user-supplied URL.",
        "cwe": "CWE-918", "top10": "A10:2021-Server-Side Request Forgery", "asvs": "V12.6.1", "wstg": "WSTG-INPV-19",
        "bad_code": "requests.get(user_url)",
        "good_code": "if parse(user_url).netloc in ALLOWED: requests.get(user_url)"
    }
]

# 2. CERT Python Dataset
CERT_DATASET = [
    {
        "id": "IDS01-P", "title": "Do not pass unsanitized user input to system commands",
        "overview": "Passing untrusted input directly to shell processes allows execution of arbitrary commands.",
        "cert": "IDS01-P", "cwe": "CWE-78", "top10": "A03:2021-Injection",
        "bad_code": "os.system('cat ' + filename)",
        "good_code": "subprocess.run(['cat', filename], check=True)"
    },
    {
        "id": "SER01-P", "title": "Do not use pickle or marshal for deserialization of untrusted data",
        "overview": "The pickle and marshal modules are insecure against erroneous or maliciously constructed data.",
        "cert": "SER01-P", "cwe": "CWE-502", "top10": "A08:2021-Software and Data Integrity Failures",
        "bad_code": "data = pickle.loads(raw_stream)",
        "good_code": "data = json.loads(raw_stream)"
    },
    {
        "id": "MSC01-P", "title": "Do not use random module for security-critical applications",
        "overview": "The standard random module uses MT19937 PRNG which is predictable.",
        "cert": "MSC01-P", "cwe": "CWE-330", "top10": "A02:2021-Cryptographic Failures",
        "bad_code": "import random; token = random.randint(1000, 9999)",
        "good_code": "import secrets; token = secrets.randbelow(9000) + 1000"
    }
]

# 3. NIST Dataset
NIST_DATASET = [
    {
        "id": "SP-800-218", "title": "Secure Software Development Framework (SSDF) v1.1",
        "overview": "Defines core software security practices organized into Prepare, Protect, Produce, and Respond.",
        "nist": "SP-800-218", "cwe": "CWE-1173", "top10": "A04:2021-Insecure Design",
        "bad_code": "# Unstructured build script skipping automated security linters",
        "good_code": "# Automated CI pipeline integrating SAST, SCA, and unit tests"
    },
    {
        "id": "SP-800-53", "title": "Security and Privacy Controls for Information Systems",
        "overview": "Catalog of security and privacy controls for federal information systems.",
        "nist": "SP-800-53", "cwe": "CWE-284", "top10": "A01:2021-Broken Access Control",
        "bad_code": "# System permitting access without identity verification",
        "good_code": "# Centralized access control enforcing MFA and RBAC"
    }
]

# 4. Security Patterns Dataset
PATTERNS_DATASET = [
    {
        "id": "Repository_Pattern", "title": "Repository Pattern",
        "overview": "Encapsulates database access behind a clean domain collection interface.",
        "pattern": "Repository_Pattern", "cwe": "CWE-89", "top10": "A03:2021-Injection",
        "bad_code": "class UserController:\n    def get(self, id): return db.execute(f'SELECT * FROM users WHERE id={id}')",
        "good_code": "class UserRepository:\n    def get(self, id): return session.query(User).filter(User.id == id).first()"
    },
    {
        "id": "Dependency_Injection", "title": "Dependency Injection Pattern",
        "overview": "Injects dependencies into classes rather than instantiating them directly.",
        "pattern": "Dependency_Injection", "cwe": "CWE-798", "top10": "A05:2021-Security Misconfiguration",
        "bad_code": "class Service:\n    def __init__(self): self.db = Database('postgres://pass@localhost/db')",
        "good_code": "class Service:\n    def __init__(self, db: Database): self.db = db"
    },
    {
        "id": "Rate_Limiting_Pattern", "title": "Rate Limiting Pattern",
        "overview": "Restricts the frequency of API invocations per client within a given window.",
        "pattern": "Rate_Limiting_Pattern", "cwe": "CWE-770", "top10": "A04:2021-Insecure Design",
        "bad_code": "@app.post('/login')\ndef login(): return auth_user()",
        "good_code": "@app.post('/login')\n@limiter.limit('5 per minute')\ndef login(): return auth_user()"
    }
]

# 5. Anti-Patterns Dataset
ANTI_PATTERNS_DATASET = [
    {
        "id": "Hardcoded_Secrets", "title": "Hardcoded Secrets Anti-Pattern",
        "overview": "Embedding passwords, private keys, or API tokens directly in source code.",
        "anti_pattern": "Hardcoded_Secrets", "cwe": "CWE-798", "top10": "A07:2021-Identification and Authentication Failures",
        "bad_code": "SECRET_KEY = 'super_secret_key_12345'",
        "good_code": "SECRET_KEY = os.environ['APP_SECRET_KEY']"
    },
    {
        "id": "Pickle_Misuse", "title": "Pickle Misuse Anti-Pattern",
        "overview": "Using Python pickle module to parse untrusted user data streams.",
        "anti_pattern": "Pickle_Misuse", "cwe": "CWE-502", "top10": "A08:2021-Software and Data Integrity Failures",
        "bad_code": "obj = pickle.loads(request.body)",
        "good_code": "obj = json.loads(request.body)"
    },
    {
        "id": "Disabled_TLS_Verification", "title": "Disabled TLS Verification Anti-Pattern",
        "overview": "Disabling SSL certificate verification in HTTP clients (`verify=False`).",
        "anti_pattern": "Disabled_TLS_Verification", "cwe": "CWE-295", "top10": "A02:2021-Cryptographic Failures",
        "bad_code": "requests.get(url, verify=False)",
        "good_code": "requests.get(url, verify='/path/to/cert.pem')"
    }
]

def render_markdown(item, doc_type, target_dir):
    item = sanitize(item, doc_type)
    file_id = item['id'].replace('-', '_').replace(' ', '_')
    filename = f"{file_id}.md"
    file_path = os.path.join(target_dir, filename)
    
    fm = f"""---
knowledge_id: KB-{file_id}
embedding_title: {item['title']} - Security Knowledge Document
official_id: {item['id']}
document_type: {doc_type}
chunk_type: concept_and_detection
title: {item['title']}
category: security
subcategory: {doc_type}
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
severity: {item['severity']}
retrieval_priority: {item['priority']}
confidence: official
tags:
  - security
  - {doc_type}
  - {item['cwe'].lower()}
keywords:
  - {item['title'].lower()}
  - {item['cwe'].lower()}
aliases:
  - {item['id']}
  - {item['title']}
related_topics:
  - {item['top10']}
  - {item['cwe']}
related_documents:
  - {item['asvs']}
  - {item['wstg']}
last_updated: 2026-07-24
---
"""
    
    body = f"""
# Retrieval Summary
This document covers {item['title']} ({item['id']}). It defines security objectives, threat models, detection guidance, AST hints, and Python code examples across FastAPI, Flask, and Django to eliminate vulnerabilities and ensure robust software assurance.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Security Objective
{item['objective']}

# Why This Matters
{item['why']}

# Threat Model
{item['threat_model']}

# Detection Guidance
AI code reviewers should scan Python source files for unvalidated usage of {item['apis']}. Look for missing authorization checks or un-parameterized dynamic input.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex Detection Hints
Use regex pattern: `{item['regex_hints']}` to flag candidate vulnerabilities.

# Semantic Detection Hints
{item['semantic_hints']}

# Relevant Python APIs
`{item['apis']}`

# Relevant Imports
`{item['imports']}`

# Vulnerable Patterns
Insecure implementation:
```python
{item['bad_code']}
```

# Secure Patterns
Secure implementation:
```python
{item['good_code']}
```

# Python Example
```python
{item['good_code']}
```

# FastAPI Example
```python
{item['fastapi']}
```

# Flask Example
```python
{item['flask']}
```

# Django Example
```python
{item['django']}
```

# SQLAlchemy Considerations
{item['sqlalchemy']}

# PostgreSQL Considerations
```sql
{item['postgresql']}
```

# Common Developer Mistakes
{item['mistakes']}

# False Positives
{item['fps']}

# False Negatives
{item['fns']}

# AI Review Heuristics
{item['heuristics']}

# Detection Confidence
Confidence level: **{item['confidence'].upper()}**

# Reasoning Chain
{item['reasoning']}

# Review Checklist
- [ ] Verify requirement for {item['id']} is enforced in code.
- [ ] Confirm automated security unit tests cover this rule.
- [ ] Ensure secure default fallback if validation fails.

# Remediation
{item['remediation']}

# Related OWASP Top 10
{item['top10']}

# Related ASVS Requirements
{item['asvs']}

# Related WSTG Tests
{item['wstg']}

# Related CWE
{item['cwe']}

# Related CERT Python Rules
{item['cert']}

# Related NIST Guidance
{item['nist']}

# Related Security Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-SEC-01: Enforce security validation and access control on all endpoints.

# Related PEPs
PEP 8 -- Style Guide for Python Code

# References
1. Official Security Standard: https://cwe.mitre.org/data/definitions/{item['cwe'].replace('CWE-', '')}.html
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [{doc_type}] document: {file_path}")

# Run generation
for item in CWE_DATASET: render_markdown(item, "cwe", CWE_DIR)
for item in CERT_DATASET: render_markdown(item, "cert_python", CERT_DIR)
for item in NIST_DATASET: render_markdown(item, "nist", NIST_DIR)
for item in PATTERNS_DATASET: render_markdown(item, "security_pattern", PATTERNS_DIR)
for item in ANTI_PATTERNS_DATASET: render_markdown(item, "anti_pattern", ANTI_PATTERNS_DIR)

print("Remaining Security Knowledge Base Builder finished successfully!")
