---
id: OWASP-A01
title: Broken Access Control - Secure Patterns
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
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
### Python - Flask / Authorized Reference Checks
```python
@app.route('/invoice/<invoice_id>')
@login_required
def get_invoice(invoice_id):
    # SECURE: Validate that the current user owns the requested invoice
    invoice = db.query("SELECT * FROM invoices WHERE id = %s AND owner_id = %s", (invoice_id, current_user.id))
    if not invoice:
        return abort(403, "Unauthorized access")
    return jsonify(invoice)
```

### Java - Spring Boot / Role-Based access control
```java
@GetMapping("/admin/delete-user/{id}")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<String> deleteUser(@PathVariable("id") Long id) {
    // SECURE: Enforces that only users with ADMIN role can delete a user
    userService.deleteUser(id);
    return ResponseEntity.ok("User deleted");
}
```

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
