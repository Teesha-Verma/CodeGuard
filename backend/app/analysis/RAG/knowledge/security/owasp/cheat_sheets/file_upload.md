---
id: OWASP-CS-file-upload
title: File Upload Cheat Sheet
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
  - file-upload
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---

# Overview
Mitigates security risks when allowing users to upload documents to servers.

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to File Upload.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
```python
# VULNERABLE: Saving file using user-provided filename on public server
file.save(os.path.join('/var/www/static', file.filename))
```

# Good Code Patterns
```python
# SECURE: Save file using secure UUID on isolated folder
filename = str(uuid.uuid4()) + ".txt"
file.save(os.path.join('/tmp/uploads', filename))
```

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
1. Rename uploaded files to UUIDs.
2. Store uploads outside the web document root.
3. Limit accepted mime-types and sizes.

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/file_upload.html
