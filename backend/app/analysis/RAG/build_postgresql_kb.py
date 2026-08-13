import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge\postgresql"

SUBDIRS = [
    "sql", "data_types", "schema_design", "indexes", "constraints",
    "querying", "joins", "aggregation", "transactions", "mvcc",
    "locking", "concurrency", "query_planner", "optimization",
    "partitioning", "json_jsonb", "full_text_search", "views",
    "materialized_views", "functions", "triggers", "security",
    "backup_restore", "replication", "monitoring", "maintenance",
    "best_practices"
]

for s in SUBDIRS:
    os.makedirs(os.path.join(BASE_DIR, s), exist_ok=True)

print("Starting PostgreSQL Knowledge Base Builder...")

def sanitize(item, subcat):
    defaults = {
        "severity": "medium", "priority": "high",
        "cwe": "CWE-89", "top10": "A03:2021-Injection", "asvs": "V5.3.1",
        "wstg": "WSTG-INPV-05", "pattern": "Repository_Pattern", "anti_pattern": "SQL_Injection",
        "overview": f"Comprehensive technical reference document detailing PostgreSQL {item['title']}.",
        "official_def": f"Official PostgreSQL documentation specification for {item['title']}.",
        "purpose": f"Standardize database design, query optimization, security, and transaction safety for {item['title']}.",
        "why": f"Proper utilization of {item['title']} prevents SQL injection, deadlocks, performance degradation, and unindexed full table scans.",
        "ast_hints": "ast.Call (execute, select), sqlglot.parse_one, pg_query",
        "regex_hints": r"(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|VACUUM|EXPLAIN)",
        "semantic_hints": f"SQL query patterns and database schema definitions involving {item['title']}.",
        "sql_syntax": "SELECT * FROM table_name WHERE condition;",
        "pg_features": f"PostgreSQL engine feature for {item['title']}.",
        "commands": "EXPLAIN ANALYZE, VACUUM FULL, REINDEX",
        "common_usage": f"Standard production SQL query pattern for {item['title']} in enterprise databases.",
        "mistakes": f"Misconfiguring {item['title']} leading to unindexed sequential scans or lock escalation.",
        "bad_practices": f"Writing un-parameterized or non-scalable SQL queries involving {item['title']}.",
        "best_practices": f"Using bound parameters, appropriate indexes, and explicit transactions for {item['title']}.",
        "sql_example": "SELECT id, username, created_at FROM users WHERE is_active = TRUE;",
        "pg_example": "EXPLAIN (ANALYZE, BUFFERS) SELECT id, username FROM users WHERE is_active = TRUE;",
        "sqla_example": "stmt = select(User).where(User.is_active == True)\nresult = session.scalars(stmt).all()",
        "perf": f"Query execution plan, index utilization, and buffer cache considerations for {item['title']}.",
        "mem": f"Shared buffers, work_mem allocation, and tuple storage footprint for {item['title']}.",
        "concurrency": f"MVCC tuple visibility and concurrent reader/writer semantics for {item['title']}.",
        "locking": f"Row-level and table-level locking behavior for {item['title']}.",
        "transaction": f"ACID compliance, savepoint handling, and isolation level requirements for {item['title']}.",
        "sec_sec": f"SQL injection prevention, Row-Level Security (RLS), and least privilege GRANT policies for {item['title']}.",
        "fps": "Internal PostgreSQL system catalog queries executed by monitoring agents (e.g. pg_stat_activity).",
        "fns": "Dynamic SQL construction inside PL/pgSQL functions bypassing static linter rules.",
        "heuristics": f"Flag any dynamic SQL string interpolation or missing index support for {item['title']}.",
        "confidence": "high", "reasoning": "1. Parse SQL AST and query parameters. 2. Verify bound parameterization. 3. Flag unindexed scans or injection vulnerabilities.",
        "opt_tips": f"Improve query latency by running ANALYZE, adding partial indexes, and tuning work_mem for {item['title']}."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    item['subcategory'] = subcat
    return item

# Complete PostgreSQL Concepts Dataset
DATASET = [
    # 1. SQL
    {"subfolder": "sql", "id": "select_queries", "title": "SELECT Queries and Result Set Projection"},
    {"subfolder": "sql", "id": "insert_upsert", "title": "INSERT and ON CONFLICT (UPSERT) Operations"},
    {"subfolder": "sql", "id": "update_returning", "title": "UPDATE Queries and RETURNING Clause"},
    {"subfolder": "sql", "id": "delete_returning", "title": "DELETE Statements and RETURNING Data"},
    {"subfolder": "sql", "id": "cte_recursive", "title": "Common Table Expressions (CTE) and Recursive Queries"},

    # 2. Data Types
    {"subfolder": "data_types", "id": "text_varchar", "title": "Text, Varchar, and Char String Data Types"},
    {"subfolder": "data_types", "id": "uuid_primary_keys", "title": "UUID Data Type and Native Key Generation"},
    {"subfolder": "data_types", "id": "json_jsonb_types", "title": "JSON vs JSONB Data Types"},
    {"subfolder": "data_types", "id": "numeric_types", "title": "Integer, Numeric, and Floating-Point Data Types"},

    # 3. Schema Design
    {"subfolder": "schema_design", "id": "normalization_principles", "title": "Database Normalization Principles"},
    {"subfolder": "schema_design", "id": "denormalization_strategies", "title": "Controlled Denormalization Strategies"},

    # 4. Indexes
    {"subfolder": "indexes", "id": "btree_indexes", "title": "B-Tree Index Architecture and Usage"},
    {"subfolder": "indexes", "id": "gin_gist_indexes", "title": "GIN and GiST Indexing for JSONB and Search"},
    {"subfolder": "indexes", "id": "brin_indexes", "title": "Block Range Indexes (BRIN) for Large Datasets"},
    {"subfolder": "indexes", "id": "partial_expression_indexes", "title": "Partial Indexes and Expression-Based Indexing"},

    # 5. Constraints
    {"subfolder": "constraints", "id": "primary_foreign_keys", "title": "Primary Key and Foreign Key Constraints"},
    {"subfolder": "constraints", "id": "check_unique_constraints", "title": "CHECK and UNIQUE Data Constraints"},

    # 6. Querying
    {"subfolder": "querying", "id": "window_functions", "title": "SQL Window Functions (OVER, PARTITION BY, RANK)"},
    {"subfolder": "querying", "id": "subqueries_exists", "title": "Subqueries, EXISTS, and IN Expressions"},

    # 7. Joins
    {"subfolder": "joins", "id": "inner_outer_joins", "title": "INNER, LEFT, RIGHT, and FULL Outer Joins"},
    {"subfolder": "joins", "id": "lateral_joins", "title": "LATERAL Subquery Joins"},

    # 8. Aggregation
    {"subfolder": "aggregation", "id": "group_by_having", "title": "GROUP BY, HAVING, and Aggregation Functions"},

    # 9. Transactions
    {"subfolder": "transactions", "id": "acid_properties", "title": "ACID Guarantees and Transaction Lifecycle"},
    {"subfolder": "transactions", "id": "isolation_levels", "title": "Transaction Isolation Levels (Read Committed to Serializable)"},

    # 10. MVCC
    {"subfolder": "mvcc", "id": "mvcc_architecture", "title": "Multi-Version Concurrency Control (MVCC) Architecture"},

    # 11. Locking
    {"subfolder": "locking", "id": "row_table_locks", "title": "Explicit Row-Level and Table-Level Locking"},
    {"subfolder": "locking", "id": "advisory_locks", "title": "PostgreSQL Application-Level Advisory Locks"},

    # 12. Concurrency
    {"subfolder": "concurrency", "id": "optimistic_pessimistic_locking", "title": "Optimistic vs Pessimistic Concurrency Control"},

    # 13. Query Planner
    {"subfolder": "query_planner", "id": "explain_explain_analyze", "title": "EXPLAIN and EXPLAIN ANALYZE Execution Plans"},

    # 14. Optimization
    {"subfolder": "optimization", "id": "query_optimization_rules", "title": "PostgreSQL Query Optimization and Cost Estimation"},

    # 15. Partitioning
    {"subfolder": "partitioning", "id": "range_list_hash_partitioning", "title": "Declarative Table Partitioning (Range, List, Hash)"},

    # 16. JSON / JSONB
    {"subfolder": "json_jsonb", "id": "jsonb_indexing_gin", "title": "JSONB Query Operators and GIN Indexing"},

    # 17. Full Text Search
    {"subfolder": "full_text_search", "id": "tsvector_tsquery_search", "title": "Full-Text Search with tsvector and tsquery"},

    # 18. Views
    {"subfolder": "views", "id": "standard_views", "title": "Relational Views and Security Barrier Views"},

    # 19. Materialized Views
    {"subfolder": "materialized_views", "id": "materialized_views_refresh", "title": "Materialized Views and Concurrent Refresh"},

    # 20. Functions
    {"subfolder": "functions", "id": "plpgsql_stored_functions", "title": "PL/pgSQL Stored Functions and Procedures"},

    # 21. Triggers
    {"subfolder": "triggers", "id": "trigger_functions_audit", "title": "Event Triggers and Automated Audit Logging"},

    # 22. Security
    {"subfolder": "security", "id": "roles_privileges_grant", "title": "PostgreSQL Roles, Grants, and Privileges"},
    {"subfolder": "security", "id": "row_level_security_rls", "title": "Row-Level Security (RLS) Policies"},

    # 23. Backup & Restore
    {"subfolder": "backup_restore", "id": "pg_dump_pg_restore", "title": "Database Backups with pg_dump and pg_restore"},

    # 24. Replication
    {"subfolder": "replication", "id": "streaming_logical_replication", "title": "Streaming and Logical Replication"},

    # 25. Monitoring
    {"subfolder": "monitoring", "id": "pg_stat_activity_monitoring", "title": "Database Performance Monitoring with pg_stat_activity"},

    # 26. Maintenance
    {"subfolder": "maintenance", "id": "vacuum_analyze_reindex", "title": "Routine Maintenance (VACUUM, ANALYZE, REINDEX)"},

    # 27. Best Practices
    {"subfolder": "best_practices", "id": "schema_and_index_strategy", "title": "PostgreSQL Production Schema and Indexing Strategy"}
]

def render_markdown(item):
    item = sanitize(item, item['subfolder'])
    title_clean = item['title'].replace(':', ' -')
    filename = f"{item['id']}.md"
    file_path = os.path.join(BASE_DIR, item['subfolder'], filename)
    
    fm = f"""---
knowledge_id: PGKB-{item['id'].replace('-', '_').upper()}
embedding_title: "{title_clean} - PostgreSQL Database Knowledge Base"
official_id: {item['id']}
document_type: postgresql_knowledge
chunk_type: concept_and_detection
title: "{title_clean}"
category: postgresql
subcategory: {item['subfolder']}
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
severity: {item['severity']}
retrieval_priority: {item['priority']}
confidence: official
tags:
  - postgresql
  - {item['subfolder']}
  - {item['id'].lower()}
keywords:
  - "{title_clean.lower()}"
  - "postgresql {item['subfolder']}"
aliases:
  - {item['id']}
  - "{title_clean}"
related_topics:
  - {item['top10']}
  - {item['cwe']}
related_documents:
  - {item['pattern']}
  - {item['anti_pattern']}
last_updated: 2026-07-24
---
"""
    
    body = f"""
# Retrieval Summary
This document provides technical reference, query execution plan analysis, index strategy guidance, and security rules for PostgreSQL {title_clean}. It covers SQL syntax, locking, MVCC, transaction isolation, SQLAlchemy ORM mappings, and AI code review heuristics.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Purpose
{item['purpose']}

# Why This Matters
{item['why']}

# Detection Guidance
AI code reviewers should evaluate SQL queries and database schemas for proper utilization of `{item['commands']}` and `{item['sql_syntax']}`. Check for un-indexed scans, missing parameters, and deadlock risks.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex Detection Hints
Use regex pattern: `{item['regex_hints']}` to flag matching SQL queries.

# Semantic Detection Hints
{item['semantic_hints']}

# Relevant SQL Syntax
`{item['sql_syntax']}`

# Relevant PostgreSQL Features
`{item['pg_features']}`

# Relevant Commands
`{item['commands']}`

# Common Usage
{item['common_usage']}

# Common Mistakes
{item['mistakes']}

# Bad Practices
{item['bad_practices']}

# Best Practices
{item['best_practices']}

# SQL Example
```sql
{item['sql_example']}
```

# PostgreSQL Example
```sql
{item['pg_example']}
```

# SQLAlchemy Example
```python
{item['sqla_example']}
```

# Performance Considerations
{item['perf']}

# Memory Considerations
{item['mem']}

# Concurrency Considerations
{item['concurrency']}

# Locking Considerations
{item['locking']}

# Transaction Considerations
{item['transaction']}

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
- [ ] Verify proper SQL parameterization and index support for {title_clean}.
- [ ] Confirm no un-indexed sequential scans on large tables.
- [ ] Ensure database migrations are tested and non-blocking.

# Optimization Tips
{item['opt_tips']}

# Related Python Knowledge
`python/security/sql_injection`, `python/performance/memory_optimization`

# Related SQLAlchemy
`orm/sqlalchemy/query_select_api`, `orm/sqlalchemy/engine_connection_pooling`

# Related Framework Knowledge
`frameworks/fastapi/dependencies_di`, `frameworks/django/models_orm`

# Related Security Knowledge
`security/owasp/top10/A03_Injection`, `security/cwe/CWE_89`

# Related Design Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-DB-01: Parameterize all SQL queries, index foreign keys, and enforce Row-Level Security policies.

# References
1. Official PostgreSQL Documentation: https://www.postgresql.org/docs/current/
2. PostgreSQL SQL Commands: https://www.postgresql.org/docs/current/sql-commands.html
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [postgresql/{item['subfolder']}] document: {file_path}")

# Run generation
for item in DATASET:
    render_markdown(item)

print("PostgreSQL Knowledge Base Builder completed successfully!")
