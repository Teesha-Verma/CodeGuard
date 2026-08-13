---
id: OWASP-A04
title: Insecure Design - Secure Patterns
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: high
priority: high
tags:
  - design
  - architecture
  - threat-modeling
  - defense-in-depth
source: OWASP Top 10 2021
source_url: https://owasp.org/Top10/A04_2021-Insecure_Design/
version: 2021
last_updated: 2026-07-19
related:
  - CWE-269
  - CWE-601
  - CWE-657
  - CWE-1173
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
### Python - Multi-step Secure Password Reset with Expiry
```python
def request_password_reset(email):
    # SECURE: Send a high-entropy, short-lived verification token via email
    token = generate_secure_token()
    save_token_with_expiry(email, token, expiry=15 * 60) # 15 mins
    send_reset_email(email, token)
    return "If the email exists, a reset link has been sent."
```

### Java - Standard Authorization Framework
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        // SECURE: Centralized, audited, and declarative access control configuration
        http.authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated()
        );
        return http.build();
    }
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
