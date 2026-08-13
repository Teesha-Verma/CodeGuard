import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge\testing"

SUBDIRS = [
    "fundamentals", "pytest", "unittest", "fixtures", "mocking",
    "assertions", "parametrization", "integration_testing", "unit_testing",
    "functional_testing", "api_testing", "database_testing", "async_testing",
    "property_based_testing", "performance_testing", "load_testing",
    "regression_testing", "security_testing", "test_design", "coverage",
    "test_doubles", "test_data", "ci_testing", "best_practices"
]

for s in SUBDIRS:
    os.makedirs(os.path.join(BASE_DIR, s), exist_ok=True)

print("Starting Testing Knowledge Base Builder...")

def sanitize(item, subcat):
    defaults = {
        "severity": "medium", "priority": "high",
        "pep": "PEP 8", "sec_know": "Security_Misconfiguration",
        "pattern": "Test_Fixture_Pattern", "anti_pattern": "Flaky_Test",
        "overview": f"Comprehensive technical reference document detailing software testing concept: {item['title']}.",
        "official_def": f"Official software quality assurance and testing specification for {item['title']}.",
        "purpose": f"Standardize automated testing, regression prevention, test reliability, and code coverage for {item['title']}.",
        "why": f"Proper implementation of {item['title']} prevents production regressions, flaky test suites, and un-tested edge cases.",
        "ast_hints": "ast.FunctionDef (test_*), ast.ClassDef (Test*), ast.Decorator (@pytest.mark)",
        "regex_hints": r"(?i)(def test_|class Test|pytest|unittest|mock|assert)",
        "semantic_hints": f"Automated test function implementations and fixture setups for {item['title']}.",
        "apis": "pytest.fixture, unittest.TestCase, unittest.mock.patch, pytest.raises",
        "fw_apis": "fastapi.testclient.TestClient, django.test.TestCase, flask.testing.FlaskClient",
        "imports": "import pytest, from unittest.mock import Mock, MagicMock, AsyncMock",
        "common_usage": f"Standard production test suite setup for {item['title']} in enterprise Python applications.",
        "mistakes": f"Misusing {item['title']} by introducing shared mutable state, network dependencies, or flaky assertions.",
        "bad_practices": f"Writing slow, non-isolated, or non-deterministic tests for {item['title']}.",
        "best_practices": f"Adhering to AAA pattern, fast execution, explicit assertions, and deterministic test doubles for {item['title']}.",
        "py_example": "def test_user_creation():\n    # AAA Pattern\n    user = User(username='test', email='test@example.com')\n    assert user.username == 'test'\n    assert user.is_active is True",
        "fw_example": "def test_read_main(client: TestClient):\n    response = client.get('/')\n    assert response.status_code == 200\n    assert response.json() == {'msg': 'Hello World'}",
        "sqla_example": "def test_create_db_user(db_session: Session):\n    user = User(username='db_user')\n    db_session.add(user)\n    db_session.commit()\n    assert user.id is not None",
        "perf": f"Test execution speed, setup/teardown latency, and parallel execution (pytest-xdist) for {item['title']}.",
        "mem": f"CPython object allocation in fixture scopes and memory leak prevention during test runs for {item['title']}.",
        "thread_safety": f"Thread safety semantics in parallel test runners and shared test state isolation for {item['title']}.",
        "async_sec": f"Behavior of pytest-asyncio and coroutine isolation for {item['title']}.",
        "sec_sec": f"Testing security boundaries, credentials masking, and fuzzing payloads for {item['title']}.",
        "fps": "Legitimate benchmark test runners or performance profiling suite hooks.",
        "fns": "Implicitly skipped tests or un-asserted async coroutines hiding regression failures.",
        "heuristics": f"Flag any missing assertions, hardcoded external API URLs, or non-deterministic sleep calls in {item['title']}.",
        "confidence": "high", "reasoning": "1. Inspect test function AST. 2. Verify assertion count and fixture isolation. 3. Flag flaky test smells.",
        "opt_tips": f"Optimize test suite runtime by reusing session-scoped fixtures and isolating database transactions for {item['title']}."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    item['subcategory'] = subcat
    return item

# Testing Concepts Dataset
DATASET = [
    # Fundamentals
    {"subfolder": "fundamentals", "id": "testing_pyramid", "title": "The Testing Pyramid (Unit, Integration, E2E)"},
    {"subfolder": "fundamentals", "id": "aaa_pattern", "title": "Arrange-Act-Assert (AAA) Pattern"},
    {"subfolder": "fundamentals", "id": "first_principles", "title": "FIRST Principles of Unit Testing"},

    # Pytest
    {"subfolder": "pytest", "id": "pytest_fixtures_scope", "title": "Pytest Fixtures Architecture and Scopes"},
    {"subfolder": "pytest", "id": "pytest_marks_plugins", "title": "Pytest Marks, Custom Flags, and Plugin Ecosystem"},
    {"subfolder": "pytest", "id": "pytest_hooks", "title": "Pytest Hook Specification and Test Lifecycle"},

    # Unittest
    {"subfolder": "unittest", "id": "unittest_testcase_suite", "title": "Standard Unittest TestCase and TestSuite Structure"},
    {"subfolder": "unittest", "id": "unittest_runner_setup", "title": "Unittest TestRunner Setup and Teardown Hooks"},

    # Fixtures
    {"subfolder": "fixtures", "id": "fixture_factories", "title": "Dynamic Fixture Factories and Yield Teardowns"},
    {"subfolder": "fixtures", "id": "monkeypatch_usage", "title": "Pytest Monkeypatch Fixture for Environment and Attributes"},

    # Mocking
    {"subfolder": "mocking", "id": "mock_magicmock_asyncmock", "title": "Mock, MagicMock, and AsyncMock Usage"},
    {"subfolder": "mocking", "id": "patch_decorator_context", "title": "Unittest.mock Patch Decorators and Context Managers"},

    # Assertions
    {"subfolder": "assertions", "id": "pytest_raises_assertions", "title": "Pytest Exception Assertions (pytest.raises, match)"},
    {"subfolder": "assertions", "id": "custom_assertion_helpers", "title": "Custom Assertion Helpers and Rich Comparison Messages"},

    # Parametrization
    {"subfolder": "parametrization", "id": "pytest_mark_parametrize", "title": "Pytest Parametrization (@pytest.mark.parametrize)"},

    # Integration & Unit
    {"subfolder": "integration_testing", "id": "integration_test_boundaries", "title": "Integration Test Boundaries and External Service Mocks"},
    {"subfolder": "unit_testing", "id": "unit_test_isolation", "title": "Unit Test Isolation and Speed Optimization"},
    {"subfolder": "functional_testing", "id": "functional_component_testing", "title": "Functional Component Testing"},

    # API & Database
    {"subfolder": "api_testing", "id": "fastapi_testclient_api", "title": "FastAPI TestClient and HTTP Endpoint Verification"},
    {"subfolder": "api_testing", "id": "django_flask_test_clients", "title": "Django and Flask Test Client Integration"},
    {"subfolder": "database_testing", "id": "sqlalchemy_db_session_fixtures", "title": "SQLAlchemy Transactional Database Test Fixtures"},
    {"subfolder": "database_testing", "id": "testcontainers_docker_db", "title": "Testcontainers Dockerized Database Testing"},

    # Async & Property Based
    {"subfolder": "async_testing", "id": "pytest_asyncio_coroutine_tests", "title": "Asyncio Coroutine Testing with pytest-asyncio"},
    {"subfolder": "property_based_testing", "id": "hypothesis_property_testing", "title": "Property-Based Testing with Hypothesis"},

    # Performance, Load, Regression
    {"subfolder": "performance_testing", "id": "locust_benchmark_performance", "title": "Performance Benchmarking and pytest-benchmark"},
    {"subfolder": "load_testing", "id": "load_stress_concurrency_testing", "title": "Load, Stress, and Concurrency Testing"},
    {"subfolder": "regression_testing", "id": "snapshot_golden_master_testing", "title": "Snapshot and Golden Master Testing"},
    {"subfolder": "security_testing", "id": "security_fuzzing_injection_testing", "title": "Automated Security Fuzzing and Injection Testing"},

    # Test Design & Coverage
    {"subfolder": "test_design", "id": "test_flakiness_prevention", "title": "Flaky Test Detection and Prevention Strategies"},
    {"subfolder": "coverage", "id": "branch_statement_coverage", "title": "Code Coverage Analysis (Coverage.py, Branch Coverage)"},
    {"subfolder": "test_doubles", "id": "spies_stubs_fakes_dummies", "title": "Test Doubles Taxonomy (Spies, Stubs, Fakes, Dummies)"},
    {"subfolder": "test_data", "id": "factory_boy_test_factories", "title": "Test Data Generation with Factory Boy"},
    {"subfolder": "ci_testing", "id": "ci_cd_test_runner_integration", "title": "CI/CD Automated Test Runner Pipelines"},
    {"subfolder": "best_practices", "id": "testing_best_practices_checklist", "title": "Enterprise Test Automation Best Practices Checklist"}
]

def render_markdown(item):
    item = sanitize(item, item['subfolder'])
    title_clean = item['title'].replace(':', ' -')
    filename = f"{item['id']}.md"
    file_path = os.path.join(BASE_DIR, item['subfolder'], filename)
    
    fm = f"""---
knowledge_id: TSTKB-{item['id'].replace('-', '_').upper()}
embedding_title: "{title_clean} - CodeGuard V2 Knowledge Base"
official_id: {item['id']}
document_type: testing_knowledge
chunk_type: concept_and_detection
title: "{title_clean}"
category: testing
subcategory: {item['subfolder']}
version: 1.0.0
source: Official Python Testing Documentation
canonical_url: https://docs.pytest.org/
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
  - testing
  - {item['subfolder']}
  - {item['id'].lower()}
keywords:
  - "{title_clean.lower()}"
  - "testing standards"
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
This document provides comprehensive technical reference, static analysis guidelines, and production best practices for {title_clean} in TESTING. It details test fixture design, AST detection hints, code examples across Python, FastAPI, and SQLAlchemy, performance tuning, and automated code review enforcement.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Purpose
{item['purpose']}

# Why This Matters
{item['why']}

# Detection Guidance
AI code reviewers should evaluate test suites for proper usage of `{item['apis']}` and `{item['fw_apis']}`. Check for un-asserted test cases, flaky network calls, and missing cleanup hooks.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex Detection Hints
Use regex pattern: `{item['regex_hints']}` to flag matching test code blocks.

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
- [ ] Verify AAA pattern and assertion presence for {title_clean}.
- [ ] Confirm zero network or external database leaks in unit tests.
- [ ] Ensure test suite executes fast and deterministically.

# Optimization Tips
{item['opt_tips']}

# Related Python Knowledge
`python/language/functions`, `python/async/coroutines`

# Related Standard Library
`unittest`, `unittest.mock`, `typing`, `sys`

# Related PEPs
{item['pep']}

# Related Security Knowledge
{item['sec_know']}

# Related Design Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-TST-01: Enforce high test coverage, deterministic fixtures, and strict separation between unit and integration tests.

# References
1. Official Pytest Documentation: https://docs.pytest.org/
2. Python Unittest Documentation: https://docs.python.org/3/library/unittest.html
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [testing/{item['subfolder']}] document: {file_path}")

# Run generation
for item in DATASET:
    render_markdown(item)

print("Testing Knowledge Base Builder completed successfully!")
