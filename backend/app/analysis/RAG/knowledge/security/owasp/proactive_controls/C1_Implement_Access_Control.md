---
id: OWASP-C1
title: Implement Access Control
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: medium
priority: medium
tags:
  - proactive-control
  - implement-access-control
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - CWE-285, OWASP A01
---

# Overview
Define and enforce access permissions for objects and operations. Deny by default.

# Why it matters
Access control forms the primary barrier preventing unauthorized access and privilege escalation.

# Detection Rules
Confirm that all application routes are protected by access rules. Run permission validation checks.

# Bad Code Patterns
```python
# VULNERABLE: Route exposes operation without check
def delete_item(item_id):
    db.delete(item_id)
```

# Good Code Patterns
```python
# SECURE: Route validates permissions and context
@require_permission('delete_items')
def delete_item(item_id, user):
    db.delete_item(item_id, user.id)
```

# Common Mistakes
Relying on URL-based protection only. Forgetting to validate access on individual object instances.

# Secure Alternatives
Use Role-Based (RBAC) or Attribute-Based Access Control (ABAC) models.

# Framework Notes
Implement global authentication guards.

# Performance Considerations
Cache access decision rules to speed up request authorization.

# Related Standards
CWE-285, OWASP A01

# References
OWASP Proactive Controls C1
