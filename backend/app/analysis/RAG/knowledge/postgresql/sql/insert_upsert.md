---
knowledge_id: PGKB-INSERT_UPSERT
embedding_title: "INSERT and ON CONFLICT (UPSERT) Operations - PostgreSQL Database Knowledge Base"
official_id: insert_upsert
document_type: postgresql_knowledge
chunk_type: concept_and_detection
title: "INSERT and ON CONFLICT (UPSERT) Operations"
category: postgresql
subcategory: sql
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
  - sql
  - insert_upsert
keywords:
  - "insert and on conflict (upsert) operations"
  - "postgresql sql"
aliases:
  - insert_upsert
  - "INSERT and ON CONFLICT (UPSERT) Operations"
related_topics:
  - A03:2021-Injection
  - CWE-89
related_documents:
  - Repository_Pattern
  - SQL_Injection
last_updated: 2026-07-24
---

# Retrieval Summary
This document provides technical reference, query execution plan analysis, index strategy guidance, and security rules for PostgreSQL INSERT and ON CONFLICT (UPSERT) Operations. It covers SQL syntax, locking, MVCC, transaction isolation, SQLAlchemy ORM mappings, and AI code review heuristics.

# Overview
Comprehensive technical reference document detailing PostgreSQL INSERT and ON CONFLICT (UPSERT) Operations.

# Official Definition
Official PostgreSQL documentation specification for INSERT and ON CONFLICT (UPSERT) Operations.

# Purpose
Standardize database design, query optimization, security, and transaction safety for INSERT and ON CONFLICT (UPSERT) Operations.

# Why This Matters
Proper utilization of INSERT and ON CONFLICT (UPSERT) Operations prevents SQL injection, deadlocks, performance degradation, and unindexed full table scans.

# Detection Guidance
AI code reviewers should evaluate SQL queries and database schemas for proper utilization of `EXPLAIN ANALYZE, VACUUM FULL, REINDEX` and `SELECT * FROM table_name WHERE condition;`. Check for un-indexed scans, missing parameters, and deadlock risks.

# AST Detection Hints
Target AST nodes: `ast.Call (execute, select), sqlglot.parse_one, pg_query`.

# Regex Detection Hints
Use regex pattern: `(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|VACUUM|EXPLAIN)` to flag matching SQL queries.

# Semantic Detection Hints
SQL query patterns and database schema definitions involving INSERT and ON CONFLICT (UPSERT) Operations.

# Relevant SQL Syntax
`SELECT * FROM table_name WHERE condition;`

# Relevant PostgreSQL Features
`PostgreSQL engine feature for INSERT and ON CONFLICT (UPSERT) Operations.`

# Relevant Commands
`EXPLAIN ANALYZE, VACUUM FULL, REINDEX`

# Common Usage
Standard production SQL query pattern for INSERT and ON CONFLICT (UPSERT) Operations in enterprise databases.

# Common Mistakes
Misconfiguring INSERT and ON CONFLICT (UPSERT) Operations leading to unindexed sequential scans or lock escalation.

# Bad Practices
Writing un-parameterized or non-scalable SQL queries involving INSERT and ON CONFLICT (UPSERT) Operations.

# Best Practices
Using bound parameters, appropriate indexes, and explicit transactions for INSERT and ON CONFLICT (UPSERT) Operations.

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
Query execution plan, index utilization, and buffer cache considerations for INSERT and ON CONFLICT (UPSERT) Operations.

# Memory Considerations
Shared buffers, work_mem allocation, and tuple storage footprint for INSERT and ON CONFLICT (UPSERT) Operations.

# Concurrency Considerations
MVCC tuple visibility and concurrent reader/writer semantics for INSERT and ON CONFLICT (UPSERT) Operations.

# Locking Considerations
Row-level and table-level locking behavior for INSERT and ON CONFLICT (UPSERT) Operations.

# Transaction Considerations
ACID compliance, savepoint handling, and isolation level requirements for INSERT and ON CONFLICT (UPSERT) Operations.

# Security Considerations
SQL injection prevention, Row-Level Security (RLS), and least privilege GRANT policies for INSERT and ON CONFLICT (UPSERT) Operations.

# Common Developer Mistakes
Misconfiguring INSERT and ON CONFLICT (UPSERT) Operations leading to unindexed sequential scans or lock escalation.

# False Positives
Internal PostgreSQL system catalog queries executed by monitoring agents (e.g. pg_stat_activity).

# False Negatives
Dynamic SQL construction inside PL/pgSQL functions bypassing static linter rules.

# AI Review Heuristics
Flag any dynamic SQL string interpolation or missing index support for INSERT and ON CONFLICT (UPSERT) Operations.

# Detection Confidence
Confidence level: **HIGH**

# Reasoning Chain
1. Parse SQL AST and query parameters. 2. Verify bound parameterization. 3. Flag unindexed scans or injection vulnerabilities.

# Review Checklist
- [ ] Verify proper SQL parameterization and index support for INSERT and ON CONFLICT (UPSERT) Operations.
- [ ] Confirm no un-indexed sequential scans on large tables.
- [ ] Ensure database migrations are tested and non-blocking.

# Optimization Tips
Improve query latency by running ANALYZE, adding partial indexes, and tuning work_mem for INSERT and ON CONFLICT (UPSERT) Operations.

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
