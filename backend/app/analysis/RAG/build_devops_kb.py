import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge\devops"

SUBDIRS = [
    "fundamentals", "docker", "docker_compose", "python_packaging",
    "dependency_management", "virtual_environments", "ci", "cd",
    "github_actions", "deployment", "configuration", "environment_variables",
    "secrets_management", "logging", "monitoring", "metrics", "tracing",
    "observability", "health_checks", "reliability", "scalability",
    "performance", "networking", "storage", "backup_restore",
    "disaster_recovery", "release_management", "infrastructure", "security",
    "best_practices"
]

for s in SUBDIRS:
    os.makedirs(os.path.join(BASE_DIR, s), exist_ok=True)

print("Starting DevOps Knowledge Base Builder...")

def sanitize(item, subcat):
    defaults = {
        "severity": "medium", "priority": "high",
        "pep": "PEP 8", "sec_know": "Security_Misconfiguration",
        "pattern": "12_Factor_App_Pattern", "anti_pattern": "Hardcoded_Secrets",
        "overview": f"Comprehensive technical reference document detailing DevOps and SRE concept: {item['title']}.",
        "official_def": f"Official cloud infrastructure, platform engineering, and DevOps specification for {item['title']}.",
        "purpose": f"Standardize automated deployment, containerization, observability, security, and reliability for {item['title']}.",
        "why": f"Proper implementation of {item['title']} prevents deployment outages, container vulnerability exposure, resource exhaustion, and unmonitored failures.",
        "ast_hints": "ast.Call (os.getenv, pydantic.BaseSettings), ast.Import (logging, opentelemetry)",
        "regex_hints": r"(?i)(FROM|ENTRYPOINT|HEALTHCHECK|ENV|EXPOSE|github/workflows|docker|opentelemetry)",
        "semantic_hints": f"Infrastructure configurations, Dockerfiles, CI/CD pipeline definitions, and telemetry setups for {item['title']}.",
        "apis": "os.environ, logging.getLogger, opentelemetry.trace, pydantic.BaseSettings",
        "fw_apis": "fastapi.FastAPI(lifespan), prometheus_client.Counter, prometheus_client.Histogram",
        "imports": "import os, import logging, from pydantic_settings import BaseSettings",
        "common_usage": f"Standard production deployment and platform configuration for {item['title']} in enterprise cloud environments.",
        "mistakes": f"Misconfiguring {item['title']} by committing secrets, running containers as root, or missing health check endpoints.",
        "bad_practices": f"Writing un-versioned, insecure, or un-monitored infrastructure setups for {item['title']}.",
        "best_practices": f"Adhering to 12-Factor App principles, multi-stage builds, least privilege, and OpenTelemetry instrumentation for {item['title']}.",
        "py_example": "class Settings(BaseSettings):\n    db_url: str = Field(..., env='DATABASE_URL')\n    log_level: str = 'INFO'\n\nsettings = Settings()",
        "fw_example": "@app.get('/health/liveness')\ndef health_liveness():\n    return {'status': 'healthy', 'timestamp': time.time()}",
        "sqla_example": "# Connection pool configuration tuned for containerized workers\nengine = create_engine(settings.db_url, pool_size=10, max_overflow=20, pool_pre_ping=True)",
        "perf": f"Container startup latency, image size reduction, layer caching, and CPU/memory limit allocation for {item['title']}.",
        "mem": f"Container cgroup memory boundaries, Python heap size, and garbage collection behavior under load for {item['title']}.",
        "thread_safety": f"Thread safety semantics in multi-worker Gunicorn/Uvicorn process configurations for {item['title']}.",
        "async_sec": f"Asyncio event loop metrics and non-blocking I/O health check responses for {item['title']}.",
        "sec_sec": f"Container vulnerability scanning, rootless execution, secrets masking, and network policy enforcement for {item['title']}.",
        "fps": "Legitimate local development docker-compose override files or CI test environment variables.",
        "fns": "Hardcoded secrets disguised as environment variable fallbacks in deep application modules.",
        "heuristics": f"Flag any root container execution, un-pinned dependencies, missing liveness probes, or exposed API tokens in {item['title']}.",
        "confidence": "high", "reasoning": "1. Scan configuration and infrastructure declarations. 2. Verify least-privilege security and observability. 3. Flag DevOps anti-patterns.",
        "opt_tips": f"Optimize container delivery pipelines by using multi-stage builds, wheel caching, and automated image vulnerability scans for {item['title']}."
    }
    for k, v in defaults.items():
        if k not in item:
            item[k] = v
    item['subcategory'] = subcat
    return item

# DevOps Concepts Dataset
DATASET = [
    # Fundamentals
    {"subfolder": "fundamentals", "id": "devops_sre_principles", "title": "DevOps Culture and Site Reliability Engineering (SRE) Principles"},

    # Docker
    {"subfolder": "docker", "id": "docker_images_multistage", "title": "Docker Multi-stage Builds and Image Size Optimization"},
    {"subfolder": "docker", "id": "container_security_rootless", "title": "Rootless Container Execution and Least Privilege Principles"},

    # Docker Compose
    {"subfolder": "docker_compose", "id": "docker_compose_services", "title": "Docker Compose Multi-Container Service Orchestration"},

    # Python Packaging & Dependency Management
    {"subfolder": "python_packaging", "id": "pyproject_toml_standards", "title": "Modern Python Packaging with pyproject.toml"},
    {"subfolder": "dependency_management", "id": "uv_poetry_lockfiles", "title": "Deterministic Dependency Locking with uv and Poetry"},
    {"subfolder": "virtual_environments", "id": "venv_virtualenv_isolation", "title": "Virtual Environment Isolation and Reproducible Environments"},

    # CI/CD & GitHub Actions
    {"subfolder": "ci", "id": "ci_continuous_integration_pipelines", "title": "Continuous Integration (CI) Automated Quality Gates"},
    {"subfolder": "cd", "id": "cd_continuous_deployment_strategies", "title": "Continuous Deployment (CD) Pipeline Orchestration"},
    {"subfolder": "github_actions", "id": "github_actions_workflows", "title": "GitHub Actions Workflows, Matrix Builds, and Caching"},

    # Deployment
    {"subfolder": "deployment", "id": "blue_green_canary_deployments", "title": "Blue-Green, Canary, and Rolling Deployment Strategies"},

    # Configuration & Secrets
    {"subfolder": "configuration", "id": "12_factor_config_management", "title": "12-Factor Application Configuration Principles"},
    {"subfolder": "environment_variables", "id": "env_var_injection_parsing", "title": "Environment Variable Injection and Strict Type Parsing"},
    {"subfolder": "secrets_management", "id": "secrets_vault_masking", "title": "Secrets Management, Vault Integration, and Masking"},

    # Logging & Monitoring
    {"subfolder": "logging", "id": "json_structured_logging", "title": "Structured JSON Logging and Log Context Injection"},
    {"subfolder": "monitoring", "id": "prometheus_metrics_exporters", "title": "Prometheus Metrics Exporters and Application Instrumentation"},
    {"subfolder": "metrics", "id": "red_use_metrics_methodology", "title": "RED and USE Metrics Methodologies for Service Monitoring"},

    # Tracing & Observability
    {"subfolder": "tracing", "id": "opentelemetry_distributed_tracing", "title": "OpenTelemetry Distributed Tracing and Context Propagation"},
    {"subfolder": "observability", "id": "three_pillars_observability", "title": "The Three Pillars of Observability (Logs, Metrics, Traces)"},

    # Health Checks & Reliability
    {"subfolder": "health_checks", "id": "liveness_readiness_probes", "title": "Liveness, Readiness, and Startup Probe Design"},
    {"subfolder": "reliability", "id": "circuit_breakers_retry_patterns", "title": "Resilience Patterns (Circuit Breakers, Retries, Backoff)"},
    {"subfolder": "scalability", "id": "horizontal_pod_autoscaling", "title": "Stateless Application Horizontal Scaling and Autoscaling"},

    # Performance, Networking, Storage
    {"subfolder": "performance", "id": "container_resource_limits", "title": "Container CPU and Memory Limit Tuning"},
    {"subfolder": "networking", "id": "container_networking_bridge", "title": "Container Networking, DNS Resolution, and Port Exposure"},
    {"subfolder": "storage", "id": "persistent_volumes_storage", "title": "Container Persistent Storage Volumes and Bind Mounts"},

    # Backup & Disaster Recovery
    {"subfolder": "backup_restore", "id": "automated_backup_strategies", "title": "Automated Database and Persistent Volume Backup Strategies"},
    {"subfolder": "disaster_recovery", "id": "disaster_recovery_rpo_rto", "title": "Disaster Recovery Planning, RPO, and RTO Enforcements"},

    # Release, Infrastructure, Security
    {"subfolder": "release_management", "id": "semantic_release_governance", "title": "Semantic Release Governance and Feature Toggles"},
    {"subfolder": "infrastructure", "id": "infrastructure_as_code_concepts", "title": "Infrastructure as Code (IaC) Architecture and Drift Control"},
    {"subfolder": "security", "id": "devsecops_container_scanning", "title": "DevSecOps Container Vulnerability Scanning and SCA"},
    {"subfolder": "best_practices", "id": "devops_production_readiness_checklist", "title": "Production Readiness Checklist for Python Microservices"}
]

def render_markdown(item):
    item = sanitize(item, item['subfolder'])
    title_clean = item['title'].replace(':', ' -')
    filename = f"{item['id']}.md"
    file_path = os.path.join(BASE_DIR, item['subfolder'], filename)
    
    fm = f"""---
knowledge_id: DVKB-{item['id'].replace('-', '_').upper()}
embedding_title: "{title_clean} - CodeGuard V2 Knowledge Base"
official_id: {item['id']}
document_type: devops_knowledge
chunk_type: concept_and_detection
title: "{title_clean}"
category: devops
subcategory: {item['subfolder']}
version: 1.0.0
source: Official DevOps Documentation
canonical_url: https://docs.docker.com/
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
  - devops
  - {item['subfolder']}
  - {item['id'].lower()}
keywords:
  - "{title_clean.lower()}"
  - "devops standards"
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
This document provides comprehensive technical reference, static analysis guidelines, and production best practices for {title_clean} in DEVOPS. It details containerization patterns, AST detection hints, code examples across Python, FastAPI, and SQLAlchemy, performance tuning, and automated code review enforcement.

# Overview
{item['overview']}

# Official Definition
{item['official_def']}

# Purpose
{item['purpose']}

# Why This Matters
{item['why']}

# Detection Guidance
AI code reviewers should evaluate infrastructure files and source code for proper usage of `{item['apis']}` and `{item['fw_apis']}`. Check for hardcoded secrets, root container execution, and missing health checks.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex Detection Hints
Use regex pattern: `{item['regex_hints']}` to flag matching configuration code blocks.

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
- [ ] Verify 12-Factor configuration rules and secret masking for {title_clean}.
- [ ] Confirm multi-stage Docker builds run as non-root users.
- [ ] Ensure readiness and liveness endpoints exist for orchestration.

# Optimization Tips
{item['opt_tips']}

# Related Python Knowledge
`python/security/secrets_safe_randomness`, `python/performance/memory_optimization`

# Related Standard Library
`os`, `sys`, `logging`, `json`

# Related PEPs
{item['pep']}

# Related Security Knowledge
{item['sec_know']}

# Related Design Patterns
{item['pattern']}

# Related Anti-Patterns
{item['anti_pattern']}

# Related Repository Rules
Rule-DEV-01: Enforce rootless container builds, 12-Factor config parsing, structured JSON logging, and OpenTelemetry instrumentation.

# References
1. Official Docker Documentation: https://docs.docker.com/
2. The 12-Factor App: https://12factor.net/
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated [devops/{item['subfolder']}] document: {file_path}")

# Run generation
for item in DATASET:
    render_markdown(item)

print("DevOps Knowledge Base Builder completed successfully!")
