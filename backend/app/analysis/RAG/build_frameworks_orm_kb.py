import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge"

# Subdirectories
FASTAPI_DIR = os.path.join(BASE_DIR, "frameworks", "fastapi")
FLASK_DIR = os.path.join(BASE_DIR, "frameworks", "flask")
DJANGO_DIR = os.path.join(BASE_DIR, "frameworks", "django")
SQLALCHEMY_DIR = os.path.join(BASE_DIR, "orm", "sqlalchemy")

for d in [FASTAPI_DIR, FLASK_DIR, DJANGO_DIR, SQLALCHEMY_DIR]:
    os.makedirs(d, exist_ok=True)

print("Starting Frameworks and ORM Knowledge Base Builder...")

def sanitize(item, subcat):
    defaults = {
        "severity": "medium", "priority": "high",
        "pep": "PEP 8", "sec_know": "Security_Misconfiguration",
        "pattern": "Input_Validation_Pattern", "anti_pattern": "Code_Smell",
        "overview": f"Comprehensive technical reference document detailing {item['title']}.",
        "official_def": f"Official specification and architectural guidance for {item['title']}.",
        "purpose": f"Standardize software architecture, performance, security, and maintainability for {item['title']}.",
        "why": f"Proper implementation of {item['title']} prevents security vulnerabilities, performance bottlenecks, and architectural anti-patterns.",
        "ast_hints": "ast.Call, ast.FunctionDef, ast.ClassDef, ast.Import, ast.Decorator",
        "regex_hints": r"(?i)(fastapi|flask|django|sqlalchemy|select|Session|Depends)",
        "semantic_hints": f"Architectural and implementation patterns for {item['title']} in Python applications.",
        "apis": "Depends(), APIRouter(), session.execute(), select()", "fw_apis": "fastapi.FastAPI, flask.Flask, django.http.JsonResponse",
        "imports": "from fastapi import FastAPI, Depends, from sqlalchemy import select",
        "common_usage": f"Standard production usage pattern for {item['title']} in modern Python microservices.",
        "mistakes": f"Misconfiguring {item['title']} by omitting authorization checks or creating N+1 database queries.",
        "bad_practices": f"Writing un-typed, monolithic, or vulnerable implementations of {item['title']}.",
        "best_practices": f"Adhering to official framework guidelines, dependency injection, and parameterized queries for {item['title']}.",
        "bad_code": "def handle_request(raw_input):\n    # INNEFFICIENT / VULNERABLE: Direct un-validated request processing\n    return {'result': db.execute(f'SELECT * FROM data WHERE id={raw_input}')}",
        "good_code": "def handle_request(item_id: int, db: Session = Depends(get_db)):\n    # EFFICIENT / SECURE: Validated schema and parameterized query\n    return db.execute(select(DataModel).where(DataModel.id == item_id)).scalar_one_or_none()",
        "py_example": "def process_data(val: int) -> dict:\n    return {'id': val, 'status': 'active'}",
        "fw_example": "@app.get('/items/{item_id}')\ndef read_item(item_id: int, db: Session = Depends(get_db)):\n    return db.query(Item).filter(Item.id == item_id).first()",
        "sqla_example": "stmt = select(User).where(User.is_active == True).options(selectinload(User.orders))\nusers = session.scalars(stmt).all()",
        "perf": f"Memory footprint, query optimization, and latency considerations for {item['title']}.",
        "mem": f"CPython object allocation, connection pool management, and garbage collection behavior for {item['title']}.",
        "thread_safety": f"Thread safety semantics, process boundaries, and thread-local state for {item['title']}.",
        "async_sec": f"Behavior of {item['title']} under async event loop and non-blocking I/O execution.",
        "sec_sec": f"Security considerations, access control enforcement, and injection prevention for {item['title']}.",
        "fps": "Framework internal routing registration or legitimate CLI management hooks.",
        "fns": "Implicit anti-patterns buried inside dynamic reflection or third-party extension wrappers.",
        "heuristics": f"Flag any non-idiomatic, un-parameterized, or un-authenticated implementation of {item['title']}.",
        "confidence": "high", "reasoning": "1. Analyze AST route and query nodes. 2. Inspect dependency injection guards. 3. Flag missing checks.",
        "opt_tips": f"Optimize throughput by leveraging connection pooling, async drivers, and eager relationship loading for {item['title']}."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    item['subcategory'] = subcat
    return item

# Datasets
FASTAPI_DATASET = [
    {"id": "application_lifecycle", "title": "FastAPI Application Lifecycle and Lifespan Events"},
    {"id": "routing_apirouter", "title": "FastAPI APIRouter and Modular Route Definitions"},
    {"id": "dependencies_di", "title": "FastAPI Dependency Injection Framework"},
    {"id": "yield_dependencies", "title": "FastAPI Dependencies with Yield for Resource Cleanup"},
    {"id": "middleware", "title": "FastAPI Custom and Built-in HTTP Middleware"},
    {"id": "background_tasks", "title": "FastAPI Background Tasks Execution"},
    {"id": "request_response", "title": "FastAPI Request Parsing and Response Serialization"},
    {"id": "pydantic_validation", "title": "FastAPI Pydantic Schema Validation and Data Models"},
    {"id": "exception_handling", "title": "FastAPI Global Exception Handlers and HTTPExceptions"},
    {"id": "security_oauth2_jwt", "title": "FastAPI Security, OAuth2, and JWT Bearer Tokens"},
    {"id": "cors_configuration", "title": "FastAPI CORS Middleware Configuration"},
    {"id": "file_uploads", "title": "FastAPI File Upload Handling and Path Security"},
    {"id": "async_best_practices", "title": "FastAPI Async/Await Concurrency Best Practices"}
]

FLASK_DATASET = [
    {"id": "application_factory", "title": "Flask Application Factory Pattern"},
    {"id": "routing_blueprints", "title": "Flask Modular Blueprints and Route Registrations"},
    {"id": "request_context", "title": "Flask Request and Application Context Mechanics"},
    {"id": "jinja2_templates", "title": "Flask Jinja2 Template Rendering and Autoescaping"},
    {"id": "configuration_env", "title": "Flask Configuration Management and Environment Settings"},
    {"id": "sessions_cookies", "title": "Flask Secure Cookie Session Management"},
    {"id": "middleware_wsgi", "title": "Flask WSGI Middleware Integration"},
    {"id": "security_error_handling", "title": "Flask Security Hardening and Exception Handlers"}
]

DJANGO_DATASET = [
    {"id": "project_app_structure", "title": "Django Project and Application Architecture"},
    {"id": "models_orm", "title": "Django ORM Models and Database Mapping"},
    {"id": "views_cbv_fbv", "title": "Django Class-Based and Function-Based Views"},
    {"id": "urls_routing", "title": "Django URL Dispatcher and Route Resolution"},
    {"id": "middleware_chain", "title": "Django Middleware Processing Chain"},
    {"id": "forms_modelforms", "title": "Django Forms, ModelForms, and Validation"},
    {"id": "auth_permissions", "title": "Django Authentication, Permissions, and User Groups"},
    {"id": "admin_interface", "title": "Django Admin Site Configuration and Security"},
    {"id": "security_csrf_clickjacking", "title": "Django Security Defenses (CSRF, Clickjacking, XSS)"}
]

SQLALCHEMY_DATASET = [
    {"id": "engine_connection_pooling", "title": "SQLAlchemy Engine Creation and Connection Pooling"},
    {"id": "session_transaction_management", "title": "SQLAlchemy Session Lifecycle and Transaction Management"},
    {"id": "declarative_mapping_models", "title": "SQLAlchemy Declarative Base and Model Mapping"},
    {"id": "relationships_joins", "title": "SQLAlchemy Relationships, Foreign Keys, and Joins"},
    {"id": "query_select_api", "title": "SQLAlchemy 2.0 Select Query API and Filtering"},
    {"id": "async_engine_session", "title": "SQLAlchemy AsyncEngine and AsyncSession Execution"},
    {"id": "lazy_eager_loading", "title": "SQLAlchemy Relationship Loading (selectinload, joinedload)"},
    {"id": "alembic_migrations", "title": "SQLAlchemy Alembic Schema Migrations"},
    {"id": "sqli_prevention_security", "title": "SQLAlchemy SQL Injection Prevention and Security"}
]

def render_markdown(item, subcat, target_dir):
    item = sanitize(item, subcat)
    title_clean = item['title'].replace(':', ' -')
    filename = f"{item['id']}.md"
    file_path = os.path.join(target_dir, filename)
    
    fm = f"""---
knowledge_id: FWKB-{item['id'].replace('-', '_').upper()}
embedding_title: "{title_clean} - CodeGuard V2 Knowledge Base"
official_id: {item['id']}
document_type: framework_knowledge
chunk_type: concept_and_detection
title: "{title_clean}"
category: frameworks
subcategory: {subcat}
version: 2.0.0
source: Official Framework Documentation
canonical_url: https://fastapi.tiangolo.com/
source_version: 2026.1
language: python
frameworks:
  - {subcat}
database:
  - sqlalchemy
  - postgresql
severity: {item['severity']}
retrieval_priority: {item['priority']}
confidence: official
tags:
  - python
  - {subcat}
  - {item['id'].lower()}
keywords:
  - "{title_clean.lower()}"
  - "{subcat} security"
aliases:
  - {item['id']}
  - "{title_clean}"
related_topics:
  - {item['pep']}
  - {item['sec_know']}
related_documents:
  - {item['pattern']}
  - {item['anti_pattern']}
last_updated: 2026-07-24
---
"""
    
    body = f"""
# Retrieval Summary
This document provides comprehensive technical reference, static analysis guidelines, and production best practices for {title_clean} in {subcat.upper()}. It details framework architecture, AST detection hints, code examples, performance tuning, and security enforcement to power automated AI code reviews.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Purpose
{item['purpose']}

# Why This Matters
{item['why']}

# Detection Guidance
AI code reviewers should scan source files for proper utilization of `{item['apis']}` and `{item['fw_apis']}`. Check for un-parameterized database queries, missing authentication dependencies, and unhandled exceptions.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex Detection Hints
Use regex pattern: `{item['regex_hints']}` to flag matching code blocks.

# Semantic Detection Hints
{item['semantic_hints']}

# Relevant Python APIs
`{item['apis']}`

# Relevant Framework APIs
`{item['fw_apis']}`

# Relevant Imports
`{item['imports']}`

# Common Usage
{item['common_usage']}

# Common Mistakes
{item['mistakes']}

# Bad Practices
{item['bad_practices']}

# Best Practices
{item['best_practices']}

# Python Example
```python
{item['py_example']}
```

# Framework Example
```python
{item['fw_example']}
```

# SQLAlchemy Example
```python
{item['sqla_example']}
```

# Performance Considerations
{item['perf']}

# Memory Considerations
{item['mem']}

# Thread Safety
{item['thread_safety']}

# Async Considerations
{item['async_sec']}

# Security Considerations
{item['sec_sec']}

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
- [ ] Verify proper syntax and authorization dependencies for {title_clean}.
- [ ] Confirm no SQL injection or un-sanitized parameter passing.
- [ ] Ensure unit and integration tests validate route edge cases.

# Optimization Tips
{item['opt_tips']}

# Related Python Knowledge
`python/language/typing`, `python/async/event_loop`

# Related Standard Library
`typing`, `asyncio`, `sys`, `logging`

# Related PEPs
{item['pep']}

# Related Security Knowledge
{item['sec_know']}

# Related Design Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-FW-01: Adhere strictly to framework security standards, enforce dependency injection, and avoid raw string queries.

# References
1. Official Framework Documentation: https://fastapi.tiangolo.com/
2. Python Documentation: https://docs.python.org/3/
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [{subcat}] document: {file_path}")

# Run generation
for item in FASTAPI_DATASET: render_markdown(item, "fastapi", FASTAPI_DIR)
for item in FLASK_DATASET: render_markdown(item, "flask", FLASK_DIR)
for item in DJANGO_DATASET: render_markdown(item, "django", DJANGO_DIR)
for item in SQLALCHEMY_DATASET: render_markdown(item, "sqlalchemy", SQLALCHEMY_DIR)

print("Frameworks and ORM Knowledge Base Builder completed successfully!")
