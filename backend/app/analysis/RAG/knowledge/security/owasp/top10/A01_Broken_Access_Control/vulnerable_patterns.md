---
id: OWASP-A01
title: Broken Access Control - Vulnerable Patterns
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
  - access-control
  - authorization
  - idor
  - privilege-escalation
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A01_2021-Broken_Access_Control/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-22
  - CWE-284
  - CWE-285
  - CWE-639
---

# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
### Python - Flask / IDOR
```python
@app.route('/invoice/<invoice_id>')
def get_invoice(invoice_id):
    # VULNERABLE: Direct access to record without validating owner
    invoice = db.query("SELECT * FROM invoices WHERE id = %s", invoice_id)
    return jsonify(invoice)
```

### Java - Spring Boot / Missing Authorization
```java
@GetMapping("/admin/delete-user/{id}")
public ResponseEntity<String> deleteUser(@PathVariable("id") Long id) {
    // VULNERABLE: No authorization check, any authenticated user can access this endpoint
    userService.deleteUser(id);
    return ResponseEntity.ok("User deleted");
}
```

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for secure patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
