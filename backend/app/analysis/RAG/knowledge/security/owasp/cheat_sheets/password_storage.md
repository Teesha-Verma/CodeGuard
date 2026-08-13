---
id: OWASP-CS-password-storage
title: Password Storage Cheat Sheet
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: critical
priority: high
tags:
  - cheat-sheet
  - password-storage
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Specifies algorithms and workflows for storing user passwords securely.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to Password Storage.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
hash = hashlib.sha256(password.encode()).hexdigest()
```

# Good Code Patterns
```python
# SECURE: Argon2id with salt and memory controls
ph = PasswordHasher()
hash = ph.hash(password)
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Never store passwords in plaintext or using symmetric encryption.
2. Use Argon2id, bcrypt, or PBKDF2.
3. Add unique salts and configure memory/work parameters high.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/password_storage.html
