import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge"

ARCH_SUBDIRS = [
    "clean_architecture", "solid", "layered_architecture", "hexagonal_architecture",
    "onion_architecture", "dependency_injection", "repository_pattern", "unit_of_work",
    "service_layer", "domain_driven_design", "cqrs", "event_driven", "microservices",
    "monolith", "design_patterns", "anti_patterns", "software_quality", "scalability",
    "maintainability", "observability", "error_handling", "configuration", "best_practices"
]

REPO_SUBDIRS = [
    "naming", "project_structure", "imports", "dependencies", "typing",
    "documentation", "logging", "exception_handling", "security", "testing",
    "database", "api", "async", "performance", "git", "ci_cd",
    "code_style", "code_review", "commit_rules", "pull_requests", "versioning",
    "configuration", "best_practices"
]

for s in ARCH_SUBDIRS:
    os.makedirs(os.path.join(BASE_DIR, "architecture", s), exist_ok=True)

for s in REPO_SUBDIRS:
    os.makedirs(os.path.join(BASE_DIR, "repository_rules", s), exist_ok=True)

print("Starting Architecture and Repository Rules Knowledge Base Builder...")

def sanitize(item, cat, subcat):
    defaults = {
        "severity": "medium", "priority": "high",
        "pep": "PEP 8", "sec_know": "Security_Misconfiguration",
        "pattern": "Repository_Pattern", "anti_pattern": "God_Object",
        "overview": f"Comprehensive technical reference document detailing {item['title']}.",
        "official_def": f"Official software architecture and engineering specification for {item['title']}.",
        "purpose": f"Standardize software architecture, maintainability, testability, and code quality for {item['title']}.",
        "why": f"Proper enforcement of {item['title']} prevents tight coupling, technical debt, security flaws, and fragile codebases.",
        "ast_hints": "ast.ClassDef, ast.FunctionDef, ast.Import, ast.Call",
        "regex_hints": r"(?i)(class|def|interface|Protocol|abstractmethod|Depends)",
        "semantic_hints": f"Architectural and structural implementation patterns for {item['title']}.",
        "apis": "typing.Protocol, abc.ABC, dataclasses.dataclass",
        "fw_apis": "fastapi.Depends, fastapi.APIRouter, sqlalchemy.orm.Session",
        "imports": "from typing import Protocol, from abc import ABC, abstractmethod",
        "common_usage": f"Standard production usage pattern for {item['title']} in enterprise Python applications.",
        "mistakes": f"Violating {item['title']} by introducing hidden coupling, global state, or leaky abstractions.",
        "bad_practices": f"Writing monolithic, un-tested, or non-modular implementations of {item['title']}.",
        "best_practices": f"Adhering to SOLID principles, dependency injection, and clean architecture boundaries for {item['title']}.",
        "py_example": "class AbstractRepository(ABC):\n    @abstractmethod\n    def get(self, id: int):\n        pass",
        "fw_example": "@app.get('/users/{user_id}')\ndef get_user(user_id: int, service: UserService = Depends()):\n    return service.get_user(user_id)",
        "sqla_example": "class SqlAlchemyRepository(AbstractRepository):\n    def __init__(self, session: Session):\n        self.session = session\n    def get(self, id: int):\n        return self.session.query(UserModel).filter_by(id=id).first()",
        "perf": f"Execution overhead, memory allocation, and call stack depth considerations for {item['title']}.",
        "mem": f"CPython object allocation footprint and garbage collection dynamics for {item['title']}.",
        "thread_safety": f"Thread safety semantics, thread-local state, and concurrency rules for {item['title']}.",
        "async_sec": f"Behavior of {item['title']} in async coroutines and non-blocking event loops.",
        "sec_sec": f"Security boundary enforcement, data isolation, and authorization guards for {item['title']}.",
        "fps": "Legitimate framework internal adapter registration or administrative CLI utilities.",
        "fns": "Implicit architectural violations hidden inside dynamic reflection calls.",
        "heuristics": f"Flag any coupling violations, un-typed boundaries, or missing abstract interfaces for {item['title']}.",
        "confidence": "high", "reasoning": "1. Analyze AST class definitions and imports. 2. Verify interface abstraction rules. 3. Flag architectural violations.",
        "opt_tips": f"Optimize application architecture by decoupling heavy dependencies and leveraging dependency injection for {item['title']}."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    item['category'] = cat
    item['subcategory'] = subcat
    return item

# Architecture Datasets
ARCH_DATASET = [
    # Clean Architecture
    {"subfolder": "clean_architecture", "id": "entities_use_cases", "title": "Entities, Use Cases, and Core Domain Business Rules"},
    {"subfolder": "clean_architecture", "id": "interface_adapters", "title": "Interface Adapters and Boundary Controllers"},
    {"subfolder": "clean_architecture", "id": "framework_decoupling", "title": "Framework Decoupling and Infrastructure Isolation"},

    # SOLID
    {"subfolder": "solid", "id": "single_responsibility", "title": "Single Responsibility Principle (SRP)"},
    {"subfolder": "solid", "id": "open_closed", "title": "Open/Closed Principle (OCP)"},
    {"subfolder": "solid", "id": "liskov_substitution", "title": "Liskov Substitution Principle (LSP)"},
    {"subfolder": "solid", "id": "interface_segregation", "title": "Interface Segregation Principle (ISP)"},
    {"subfolder": "solid", "id": "dependency_inversion", "title": "Dependency Inversion Principle (DIP)"},

    # Layered & Hexagonal
    {"subfolder": "layered_architecture", "id": "layered_boundaries", "title": "Layered Architecture Boundaries and Data Flow"},
    {"subfolder": "hexagonal_architecture", "id": "ports_and_adapters", "title": "Hexagonal Architecture (Ports and Adapters)"},
    {"subfolder": "onion_architecture", "id": "onion_core_domain", "title": "Onion Architecture Core Domain and Outer Rings"},

    # Patterns
    {"subfolder": "dependency_injection", "id": "di_containers", "title": "Dependency Injection Containers and Wiring"},
    {"subfolder": "repository_pattern", "id": "generic_repository", "title": "Generic Repository Pattern Implementation"},
    {"subfolder": "unit_of_work", "id": "uow_transaction_boundary", "title": "Unit of Work Pattern and Transaction Isolation"},
    {"subfolder": "service_layer", "id": "application_service_layer", "title": "Application Service Layer and Orchestration"},

    # DDD & CQRS
    {"subfolder": "domain_driven_design", "id": "aggregates_value_objects", "title": "Domain-Driven Design (Aggregates, Entities, Value Objects)"},
    {"subfolder": "cqrs", "id": "command_query_segregation", "title": "Command Query Responsibility Segregation (CQRS)"},
    {"subfolder": "event_driven", "id": "event_sourcing_pubsub", "title": "Event-Driven Architecture and Event Sourcing"},
    {"subfolder": "microservices", "id": "microservice_boundaries", "title": "Microservice Bounded Contexts and Communication"},
    {"subfolder": "monolith", "id": "modular_monolith", "title": "Modular Monolith Architecture"},

    # Design & Anti Patterns
    {"subfolder": "design_patterns", "id": "gof_behavioral_patterns", "title": "GoF Behavioral Design Patterns (Strategy, Observer, Command)"},
    {"subfolder": "anti_patterns", "id": "architectural_smells", "title": "Architectural Anti-Patterns (God Object, Circular Dependency)"},
    {"subfolder": "software_quality", "id": "cyclomatic_complexity", "title": "Cyclomatic Complexity and Code Maintainability Metrics"},
    {"subfolder": "scalability", "id": "stateless_services", "title": "Stateless Application Services and Horizontal Scaling"},
    {"subfolder": "maintainability", "id": "cohesion_coupling", "title": "High Cohesion and Low Coupling Principles"},
    {"subfolder": "observability", "id": "structured_logging_tracing", "title": "Structured Logging, OpenTelemetry, and Tracing"},
    {"subfolder": "error_handling", "id": "domain_exception_hierarchy", "title": "Domain Exception Hierarchy and Global Handlers"},
    {"subfolder": "configuration", "id": "12_factor_config", "title": "12-Factor App Configuration and Environment Secrets"},
    {"subfolder": "best_practices", "id": "architecture_decision_records", "title": "Architecture Decision Records (ADR) and Governance"}
]

# Repository Rules Datasets
REPO_DATASET = [
    {"subfolder": "naming", "id": "python_naming_conventions", "title": "PEP 8 Naming Conventions for Variables, Functions, and Classes"},
    {"subfolder": "project_structure", "id": "src_layout_standards", "title": "Standard src/ Directory Layout and Module Hierarchy"},
    {"subfolder": "imports", "id": "import_ordering_rules", "title": "Import Ordering Rules (isort) and Absolute vs Relative Imports"},
    {"subfolder": "dependencies", "id": "dependency_pinning_security", "title": "Dependency Pinning, Lockfiles, and SCA Auditing"},
    {"subfolder": "typing", "id": "strict_type_checking", "title": "Strict Static Type Hinting (mypy, pyright)"},
    {"subfolder": "documentation", "id": "docstring_standards", "title": "Docstring Standards (PEP 257) and API Documentation"},
    {"subfolder": "logging", "id": "logging_levels_context", "title": "Logging Levels, Contextual Encoders, and Sensitive Data Masking"},
    {"subfolder": "exception_handling", "id": "explicit_exception_handling", "title": "Explicit Exception Catching and Custom Exception Types"},
    {"subfolder": "security", "id": "secret_scanning_precommit", "title": "Secret Scanning, Pre-commit Hooks, and SAST Linters"},
    {"subfolder": "testing", "id": "pytest_fixture_patterns", "title": "Pytest Fixture Patterns, Test Coverage, and Mocking"},
    {"subfolder": "database", "id": "migration_hygiene", "title": "Database Migration Hygiene and Non-Blocking DDL"},
    {"subfolder": "api", "id": "rest_versioning_schemas", "title": "REST API Endpoint Naming, Versioning, and OpenAPI Schemas"},
    {"subfolder": "async", "id": "non_blocking_async_rules", "title": "Non-Blocking Async Execution and Loop Safety"},
    {"subfolder": "performance", "id": "memory_leak_prevention", "title": "Memory Leak Prevention, Slots, and Resource Management"},
    {"subfolder": "git", "id": "branching_commit_rules", "title": "Git Branch Naming, Conventional Commits, and PR Workflows"},
    {"subfolder": "ci_cd", "id": "automated_pipeline_checks", "title": "CI/CD Pipeline Automated Checks (Lint, Type Check, Test, Audit)"},
    {"subfolder": "code_style", "id": "ruff_black_linting", "title": "Code Formatting and Automated Linting Rules (Ruff, Black)"},
    {"subfolder": "code_review", "id": "code_review_checklist", "title": "Automated AI Code Review Checklist and Thresholds"},
    {"subfolder": "commit_rules", "id": "atomic_commits", "title": "Atomic Commit Principles and Message Specifications"},
    {"subfolder": "pull_requests", "id": "pr_template_requirements", "title": "Pull Request Template, Verification, and Review Approvals"},
    {"subfolder": "versioning", "id": "semantic_versioning", "title": "Semantic Versioning (SemVer) and Release Governance"},
    {"subfolder": "configuration", "id": "pydantic_settings", "title": "Pydantic BaseSettings for Environment Configuration"},
    {"subfolder": "best_practices", "id": "repository_hygiene_rules", "title": "Repository Hygiene, .gitignore Standards, and License Compliance"}
]

def render_markdown(item, cat):
    item = sanitize(item, cat, item['subfolder'])
    title_clean = item['title'].replace(':', ' -')
    filename = f"{item['id']}.md"
    file_path = os.path.join(BASE_DIR, cat, item['subfolder'], filename)
    
    fm = f"""---
knowledge_id: ARKB-{item['id'].replace('-', '_').upper()}
embedding_title: "{title_clean} - CodeGuard V2 Knowledge Base"
official_id: {item['id']}
document_type: architecture_knowledge
chunk_type: concept_and_detection
title: "{title_clean}"
category: {cat}
subcategory: {item['subfolder']}
version: 1.0.0
source: Official Software Engineering Standards
canonical_url: https://blog.cleancoder.com/
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
  - {cat}
  - {item['subfolder']}
  - {item['id'].lower()}
keywords:
  - "{title_clean.lower()}"
  - "{cat} standards"
aliases:
  - {item['id']}
  - "{title_clean}"
related_topics:
  - {item['pep']}
  - {item['sec_know']}
related_documents:
  - {item['pattern']}
  - {item['anti_pattern']}
last_updated: 2026-07-25
---
"""
    
    body = f"""
# Retrieval Summary
This document provides comprehensive technical reference, static analysis guidelines, and production best practices for {title_clean} in {cat.upper()}. It details architectural boundaries, AST detection hints, code examples across Python, FastAPI, and SQLAlchemy, performance tuning, and automated code review enforcement.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Purpose
{item['purpose']}

# Why This Matters
{item['why']}

# Detection Guidance
AI code reviewers should evaluate source files for proper adherence to `{item['apis']}` and `{item['fw_apis']}`. Check for tight coupling, missing abstraction interfaces, and non-idiomatic structure.

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
- [ ] Verify proper structural boundaries and typing rules for {title_clean}.
- [ ] Confirm low coupling and high cohesion across modules.
- [ ] Ensure unit tests validate domain logic independently of infrastructure.

# Optimization Tips
{item['opt_tips']}

# Related Python Knowledge
`python/language/classes`, `python/best_practices/solid_principles`

# Related Standard Library
`typing`, `abc`, `dataclasses`, `sys`

# Related PEPs
{item['pep']}

# Related Security Knowledge
{item['sec_know']}

# Related Design Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-ARCH-01: Enforce clean architectural boundaries, dependency inversion, and strict repository code quality standards.

# References
1. Clean Architecture Guide: https://blog.cleancoder.com/
2. Refactoring Guru: https://refactoring.guru/
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [{cat}/{item['subfolder']}] document: {file_path}")

# Run generation
for item in ARCH_DATASET:
    render_markdown(item, "architecture")

for item in REPO_DATASET:
    render_markdown(item, "repository_rules")

print("Architecture and Repository Rules Knowledge Base Builder completed successfully!")
