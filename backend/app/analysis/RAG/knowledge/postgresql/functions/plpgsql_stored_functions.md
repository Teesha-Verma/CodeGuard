---
knowledge_id: PGKB-PLPGSQL_STORED_FUNCTIONS
embedding_title: "PL/pgSQL Stored Functions and Procedures - PostgreSQL Database Knowledge Base"
official_id: plpgsql_stored_functions
document_type: postgresql_knowledge
chunk_type: concept_and_detection
title: "PL/pgSQL Stored Functions and Procedures"
category: postgresql
subcategory: functions
version: 15.0
source: Official PostgreSQL Documentation
canonical_url: https://www.postgresql.org/docs/current/
source_version: 15.4
language: sql
frameworks:
  - fastapi
  - flask
  - django
database: postgresql
severity: medium
retrieval_priority: high
confidence: official
tags:
  - postgresql
  - functions
  - plpgsql_stored_functions
keywords:
  - "pl/pgsql stored functions and procedures"
  - "postgresql functions"
aliases:
  - plpgsql_stored_functions
  - "PL/pgSQL Stored Functions and Procedures"
related_topics:
  - A03:2021-Injection
  - CWE-89
related_documents:
  - Repository_Pattern
  - SQL_Injection
last_updated: 2026-07-24
---

# Retrieval Summary
This document provides technical reference, query execution plan analysis, index strategy guidance, and security rules for PostgreSQL PL/pgSQL Stored Functions and Procedures. It covers SQL syntax, locking, MVCC, transaction isolation, SQLAlchemy ORM mappings, and AI code review heuristics.

# Overview
Comprehensive technical reference document detailing PostgreSQL PL/pgSQL Stored Functions and Procedures.

# Official Definition
Official PostgreSQL documentation specification for PL/pgSQL Stored Functions and Procedures.

# Purpose
Standardize database design, query optimization, security, and transaction safety for PL/pgSQL Stored Functions and Procedures.

# Why This Matters
Proper utilization of PL/pgSQL Stored Functions and Procedures prevents SQL injection, deadlocks, performance degradation, and unindexed full table scans.

# Detection Guidance
AI code reviewers should evaluate SQL queries and database schemas for proper utilization of `EXPLAIN ANALYZE, VACUUM FULL, REINDEX` and `SELECT * FROM table_name WHERE condition;`. Check for un-indexed scans, missing parameters, and deadlock risks.

# AST Detection Hints
Target AST nodes: `ast.Call (execute, select), sqlglot.parse_one, pg_query`.

# Regex Detection Hints
Use regex pattern: `(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|VACUUM|EXPLAIN)` to flag matching SQL queries.

# Semantic Detection Hints
SQL query patterns and database schema definitions involving PL/pgSQL Stored Functions and Procedures.

# Relevant SQL Syntax
`SELECT * FROM table_name WHERE condition;`

# Relevant PostgreSQL Features
`PostgreSQL engine feature for PL/pgSQL Stored Functions and Procedures.`

# Relevant Commands
`EXPLAIN ANALYZE, VACUUM FULL, REINDEX`

# Common Usage
Standard production SQL query pattern for PL/pgSQL Stored Functions and Procedures in enterprise databases.

# Common Mistakes
Misconfiguring PL/pgSQL Stored Functions and Procedures leading to unindexed sequential scans or lock escalation.

# Bad Practices
Writing un-parameterized or non-scalable SQL queries involving PL/pgSQL Stored Functions and Procedures.

# Best Practices
Using bound parameters, appropriate indexes, and explicit transactions for PL/pgSQL Stored Functions and Procedures.

# SQL Example
```sql
SELECT id, username, created_at FROM users WHERE is_active = TRUE;
```

# PostgreSQL Example
```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT id, username FROM users WHERE is_active = TRUE;
```

# SQLAlchemy Example
```python
stmt = select(User).where(User.is_active == True)
result = session.scalars(stmt).all()
```

# Performance Considerations
Query execution plan, index utilization, and buffer cache considerations for PL/pgSQL Stored Functions and Procedures.

# Memory Considerations
Shared buffers, work_mem allocation, and tuple storage footprint for PL/pgSQL Stored Functions and Procedures.

# Concurrency Considerations
MVCC tuple visibility and concurrent reader/writer semantics for PL/pgSQL Stored Functions and Procedures.

# Locking Considerations
Row-level and table-level locking behavior for PL/pgSQL Stored Functions and Procedures.

# Transaction Considerations
ACID compliance, savepoint handling, and isolation level requirements for PL/pgSQL Stored Functions and Procedures.

# Security Considerations
SQL injection prevention, Row-Level Security (RLS), and least privilege GRANT policies for PL/pgSQL Stored Functions and Procedures.

# Common Developer Mistakes
Misconfiguring PL/pgSQL Stored Functions and Procedures leading to unindexed sequential scans or lock escalation.

# False Positives
Internal PostgreSQL system catalog queries executed by monitoring agents (e.g. pg_stat_activity).

# False Negatives
Dynamic SQL construction inside PL/pgSQL functions bypassing static linter rules.

# AI Review Heuristics
Flag any dynamic SQL string interpolation or missing index support for PL/pgSQL Stored Functions and Procedures.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
1. Parse SQL AST and query parameters. 2. Verify bound parameterization. 3. Flag unindexed scans or injection vulnerabilities.

# Review Checklist
- [ ] Verify proper SQL parameterization and index support for PL/pgSQL Stored Functions and Procedures.
- [ ] Confirm no un-indexed sequential scans on large tables.
- [ ] Ensure database migrations are tested and non-blocking.

# Optimization Tips
Improve query latency by running ANALYZE, adding partial indexes, and tuning work_mem for PL/pgSQL Stored Functions and Procedures.

# Related Python Knowledge
`python/security/sql_injection`, `python/performance/memory_optimization`

# Related SQLAlchemy
`orm/sqlalchemy/query_select_api`, `orm/sqlalchemy/engine_connection_pooling`

# Related Framework Knowledge
`frameworks/fastapi/dependencies_di`, `frameworks/django/models_orm`

# Related Security Knowledge
`security/owasp/top10/A03_Injection`, `security/cwe/CWE_89`

# Related Design Patterns
Repository_Pattern

# Related Anti-Patterns
SQL_Injection

# Related Repository Rules
Rule-DB-01: Parameterize all SQL queries, index foreign keys, and enforce Row-Level Security policies.

# References
1. Official PostgreSQL Documentation: https://www.postgresql.org/docs/current/
2. PostgreSQL SQL Commands: https://www.postgresql.org/docs/current/sql-commands.html
