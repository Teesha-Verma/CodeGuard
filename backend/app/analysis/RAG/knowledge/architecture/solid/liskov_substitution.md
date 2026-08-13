---
knowledge_id: ARKB-LISKOV_SUBSTITUTION
embedding_title: "Liskov Substitution Principle (LSP) - CodeGuard V2 Knowledge Base"
official_id: liskov_substitution
document_type: architecture_knowledge
chunk_type: concept_and_detection
title: "Liskov Substitution Principle (LSP)"
category: architecture
subcategory: solid
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
severity: medium
retrieval_priority: high
confidence: official
tags:
  - architecture
  - solid
  - liskov_substitution
keywords:
  - "liskov substitution principle (lsp)"
  - "architecture standards"
aliases:
  - liskov_substitution
  - "Liskov Substitution Principle (LSP)"
related_topics:
  - PEP 8
  - Security_Misconfiguration
related_documents:
  - Repository_Pattern
  - God_Object
last_updated: 2026-07-25
---

# Retrieval Summary
This document provides comprehensive technical reference, static analysis guidelines, and production best practices for Liskov Substitution Principle (LSP) in ARCHITECTURE. It details architectural boundaries, AST detection hints, code examples across Python, FastAPI, and SQLAlchemy, performance tuning, and automated code review enforcement.

# Overview
Comprehensive technical reference document detailing Liskov Substitution Principle (LSP).

# Official Definition
Official software architecture and engineering specification for Liskov Substitution Principle (LSP).

# Purpose
Standardize software architecture, maintainability, testability, and code quality for Liskov Substitution Principle (LSP).

# Why This Matters
Proper enforcement of Liskov Substitution Principle (LSP) prevents tight coupling, technical debt, security flaws, and fragile codebases.

# Detection Guidance
AI code reviewers should evaluate source files for proper adherence to `typing.Protocol, abc.ABC, dataclasses.dataclass` and `fastapi.Depends, fastapi.APIRouter, sqlalchemy.orm.Session`. Check for tight coupling, missing abstraction interfaces, and non-idiomatic structure.

# AST Detection Hints
Target AST nodes: `ast.ClassDef, ast.FunctionDef, ast.Import, ast.Call`.

# Regex Detection Hints
Use regex pattern: `(?i)(class|def|interface|Protocol|abstractmethod|Depends)` to flag matching code blocks.

# Semantic Detection Hints
Architectural and structural implementation patterns for Liskov Substitution Principle (LSP).

# Relevant Python APIs
`typing.Protocol, abc.ABC, dataclasses.dataclass`

# Relevant Framework APIs
`fastapi.Depends, fastapi.APIRouter, sqlalchemy.orm.Session`

# Relevant Imports
`from typing import Protocol, from abc import ABC, abstractmethod`

# Common Usage
Standard production usage pattern for Liskov Substitution Principle (LSP) in enterprise Python applications.

# Common Mistakes
Violating Liskov Substitution Principle (LSP) by introducing hidden coupling, global state, or leaky abstractions.

# Bad Practices
Writing monolithic, un-tested, or non-modular implementations of Liskov Substitution Principle (LSP).

# Best Practices
Adhering to SOLID principles, dependency injection, and clean architecture boundaries for Liskov Substitution Principle (LSP).

# Python Example
```python
class AbstractRepository(ABC):
    @abstractmethod
    def get(self, id: int):
        pass
```

# Framework Example
```python
@app.get('/users/{user_id}')
def get_user(user_id: int, service: UserService = Depends()):
    return service.get_user(user_id)
```

# SQLAlchemy Example
```python
class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session
    def get(self, id: int):
        return self.session.query(UserModel).filter_by(id=id).first()
```

# Performance Considerations
Execution overhead, memory allocation, and call stack depth considerations for Liskov Substitution Principle (LSP).

# Memory Considerations
CPython object allocation footprint and garbage collection dynamics for Liskov Substitution Principle (LSP).

# Thread Safety
Thread safety semantics, thread-local state, and concurrency rules for Liskov Substitution Principle (LSP).

# Async Considerations
Behavior of Liskov Substitution Principle (LSP) in async coroutines and non-blocking event loops.

# Security Considerations
Security boundary enforcement, data isolation, and authorization guards for Liskov Substitution Principle (LSP).

# Common Developer Mistakes
Violating Liskov Substitution Principle (LSP) by introducing hidden coupling, global state, or leaky abstractions.

# False Positives
Legitimate framework internal adapter registration or administrative CLI utilities.

# False Negatives
Implicit architectural violations hidden inside dynamic reflection calls.

# AI Review Heuristics
Flag any coupling violations, un-typed boundaries, or missing abstract interfaces for Liskov Substitution Principle (LSP).

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
1. Analyze AST class definitions and imports. 2. Verify interface abstraction rules. 3. Flag architectural violations.

# Review Checklist
- [ ] Verify proper structural boundaries and typing rules for Liskov Substitution Principle (LSP).
- [ ] Confirm low coupling and high cohesion across modules.
- [ ] Ensure unit tests validate domain logic independently of infrastructure.

# Optimization Tips
Optimize application architecture by decoupling heavy dependencies and leveraging dependency injection for Liskov Substitution Principle (LSP).

# Related Python Knowledge
`python/language/classes`, `python/best_practices/solid_principles`

# Related Standard Library
`typing`, `abc`, `dataclasses`, `sys`

# Related PEPs
PEP 8

# Related Security Knowledge
Security_Misconfiguration

# Related Design Patterns
Repository_Pattern

# Related Anti-Patterns
God_Object

# Related Repository Rules
Rule-ARCH-01: Enforce clean architectural boundaries, dependency inversion, and strict repository code quality standards.

# References
1. Clean Architecture Guide: https://blog.cleancoder.com/
2. Refactoring Guru: https://refactoring.guru/
