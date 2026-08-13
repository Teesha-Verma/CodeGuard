import os
import json
from datetime import datetime

# Define base directory
BASE_DIR = r"d:\RAG\knowledge"

# Dictionaries of Top 10 data
TOP10_DATA = {
    "A01": {
        "title": "Broken Access Control",
        "severity": "critical",
        "priority": "high",
        "tags": ["access-control", "authorization", "idor", "privilege-escalation"],
        "source_url": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
        "cwes": ["CWE-22", "CWE-284", "CWE-285", "CWE-639"],
        "overview": "Broken Access Control occurs when users can access resources or perform actions outside of their intended permissions. Web applications fail to enforce authorization checks, allowing attackers to access unauthorized data, modify settings, or elevate privileges.",
        "why_it_matters": "Access control failures allow attackers to view sensitive records, modify data, assume administrative control, or execute functions restricted to high-privileged roles. This can result in severe data breaches and regulatory compliance violations.",
        "detection_rules": "1. Verify all endpoints enforce authorization checks based on user identity and roles.\n2. Review routing and middleware configurations to ensure access policies are applied globally.\n3. Perform manual testing for Indirect Object References (IDOR) by modifying parameters (e.g. user_id, doc_id).\n4. Run automated DAST tools to scan for endpoints accessible without authentication.",
        "bad_code_patterns": "### Python - Flask / IDOR\n```python\n@app.route('/invoice/<invoice_id>')\ndef get_invoice(invoice_id):\n    # VULNERABLE: Direct access to record without validating owner\n    invoice = db.query(\"SELECT * FROM invoices WHERE id = %s\", invoice_id)\n    return jsonify(invoice)\n```\n\n### Java - Spring Boot / Missing Authorization\n```java\n@GetMapping(\"/admin/delete-user/{id}\")\npublic ResponseEntity<String> deleteUser(@PathVariable(\"id\") Long id) {\n    // VULNERABLE: No authorization check, any authenticated user can access this endpoint\n    userService.deleteUser(id);\n    return ResponseEntity.ok(\"User deleted\");\n}\n```",
        "good_code_patterns": "### Python - Flask / Authorized Reference Checks\n```python\n@app.route('/invoice/<invoice_id>')\n@login_required\ndef get_invoice(invoice_id):\n    # SECURE: Validate that the current user owns the requested invoice\n    invoice = db.query(\"SELECT * FROM invoices WHERE id = %s AND owner_id = %s\", (invoice_id, current_user.id))\n    if not invoice:\n        return abort(403, \"Unauthorized access\")\n    return jsonify(invoice)\n```\n\n### Java - Spring Boot / Role-Based access control\n```java\n@GetMapping(\"/admin/delete-user/{id}\")\n@PreAuthorize(\"hasRole('ADMIN')\")\npublic ResponseEntity<String> deleteUser(@PathVariable(\"id\") Long id) {\n    // SECURE: Enforces that only users with ADMIN role can delete a user\n    userService.deleteUser(id);\n    return ResponseEntity.ok(\"User deleted\");\n}\n```",
        "common_mistakes": "1. Relying on client-side routing or UI hiding to enforce permissions (e.g., hiding a delete button in the UI without protecting the backend API endpoint).\n2. Hardcoding role names inside controllers rather than leveraging authorization policies or middlewares.\n3. Using sequential IDs instead of UUIDs, making it trivial for attackers to discover and harvest records via IDOR.",
        "secure_alternatives": "1. Use centralized authorization middleware or frameworks (e.g., Spring Security, FastAPI Depends).\n2. Deny access by default. Design access controls globally rather than per controller.\n3. Minimize reliance on client-provided parameters to determine resource ownership. Derive ownership from the session or token context.",
        "framework_notes": "In FastAPI, leverage dependency injection (`Depends`) to enforce access control. Use dependency classes that load the object and check user permissions before invoking controller logic. In Spring Security, use Method Security annotations such as `@PreAuthorize` or `@PostAuthorize`.",
        "performance_considerations": "Caching user permissions in memory (e.g., Redis) can significantly reduce database lookup overhead for access control checks. Ensure cache invalidation policies are robust.",
        "related_standards": "OWASP ASVS V3 (Access Control), NIST SP 800-53 AC (Access Control), ISO/IEC 27001 A.9 (Access Control).",
        "references": "1. OWASP Top 10 A01: https://owasp.org/Top10/A01_2021-Broken_Access_Control/\n2. OWASP Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html"
    },
    "A02": {
        "title": "Cryptographic Failures",
        "severity": "critical",
        "priority": "high",
        "tags": ["cryptography", "encryption", "hashing", "sensitive-data"],
        "source_url": "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
        "cwes": ["CWE-311", "CWE-327", "CWE-328", "CWE-757"],
        "overview": "Cryptographic Failures occur when sensitive data is exposed or compromised due to absent or weak cryptographic protections in transit and at rest. This includes weak cipher algorithms, hardcoded secret keys, and insufficient key protection.",
        "why_it_matters": "If sensitive data (passwords, credit card numbers, PII) is stored or transmitted without strong encryption, attackers who gain access to the database or intercept network traffic can read, steal, or tamper with the data, causing severe security breaches.",
        "detection_rules": "1. Scan code for hardcoded passwords, API keys, or secret tokens.\n2. Review cryptographic configurations to identify weak hash functions (MD5, SHA1) or obsolete ciphers (DES, RC4).\n3. Check TLS configurations on servers to ensure HTTP is disabled and strong cipher suites are enforced.\n4. Use SAST tools to flag insecure random number generators (e.g. using `random` instead of `secrets`).",
        "bad_code_patterns": "### Python - Insecure MD5 Hashing & Hardcoded Key\n```python\nimport hashlib\n\ndef hash_password(password):\n    # VULNERABLE: MD5 is broken and easily cracked\n    return hashlib.md5(password.encode()).hexdigest()\n\nSECRET_KEY = \"super_secret_key_12345\" # VULNERABLE: Hardcoded secret\n```\n\n### Java - Insecure Randomness\n```java\nimport java.util.Random;\n\npublic class InsecureKeyGenerator {\n    public int generateToken() {\n        // VULNERABLE: Insecure pseudo-random number generator\n        Random r = new Random();\n        return r.nextInt();\n    }\n}\n```",
        "good_code_patterns": "### Python - Secure Argon2 Hashing & Environment Config\n```python\nfrom argon2 import PasswordHasher\nimport os\n\nph = PasswordHasher()\n\ndef hash_password(password):\n    # SECURE: Argon2 is a robust password hashing algorithm\n    return ph.hash(password)\n\n# SECURE: Read key from environment variable\nSECRET_KEY = os.environ.get(\"APP_SECRET_KEY\")\n```\n\n### Java - Secure Cryptographic Randomness\n```java\nimport java.security.SecureRandom;\n\npublic class SecureKeyGenerator {\n    public int generateToken() {\n        // SECURE: Cryptographically strong random number generator\n        SecureRandom sr = new SecureRandom();\n        return sr.nextInt();\n    }\n}\n```",
        "common_mistakes": "1. Storing passwords using reversible encryption instead of salted, one-way hashes.\n2. Generating cryptographic keys with insufficient entropy or predictable seeds.\n3. Using HTTP for administrative panels or web service APIs, allowing sniffing of session tokens.",
        "secure_alternatives": "1. Use standardized libraries (e.g. `cryptography` in Python, JCA in Java) rather than implementing custom crypto.\n2. Hash passwords using Argon2id, bcrypt, or PBKDF2 with adequate salt and iterations.\n3. Always encrypt sensitive data at rest using AES-256-GCM or AES-256-CBC.",
        "framework_notes": "In Spring Boot, integrate Spring Security's `BCryptPasswordEncoder` or `Argon2PasswordEncoder`. In Python, use `passlib` or `argon2-cffi` for password hashing and validation.",
        "performance_considerations": "Argon2 and bcrypt are deliberately CPU-intensive to resist brute-force attacks. Tune work factors (iterations/memory) to balance security and responsiveness.",
        "related_standards": "ASVS V2 (Communications Security), FIPS 140-3, PCI-DSS Requirement 3 (Protect stored cardholder data).",
        "references": "1. OWASP Top 10 A02: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/\n2. OWASP Cryptographic Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"
    },
    "A03": {
        "title": "Injection",
        "severity": "critical",
        "priority": "high",
        "tags": ["injection", "sqli", "command-injection", "input-validation"],
        "source_url": "https://owasp.org/Top10/A03_2021-Injection/",
        "cwes": ["CWE-78", "CWE-89", "CWE-94", "CWE-562"],
        "overview": "Injection vulnerabilities occur when untrusted user input is sent to an interpreter as part of a command or query. The attacker's hostile data tricks the interpreter into executing unintended commands or accessing data without proper authorization.",
        "why_it_matters": "Injection can result in data loss, corruption, disclosure to unauthorized parties, lack of accountability, or denial of service. In severe cases, SQL injection can lead to database takeover, and OS command injection can lead to remote code execution.",
        "detection_rules": "1. Identify all instances of dynamic SQL statements constructed via string formatting or concatenation.\n2. Use SAST tools to trace user input from endpoints (sources) to database execution or shell invocation (sinks).\n3. Test for SQLi using automated tools (e.g. sqlmap) or manual payload injection.\n4. Review input validation layers and parameterized query configurations.",
        "bad_code_patterns": "### Python - Raw SQL Concatenation\n```python\ndef get_user_data(username):\n    # VULNERABLE: Direct SQL injection\n    query = f\"SELECT * FROM users WHERE username = '{username}'\"\n    return db.execute(query)\n```\n\n### Java - Raw Process Exec\n```java\npublic void executePing(String ip) throws IOException {\n    // VULNERABLE: OS command injection\n    Runtime.getRuntime().exec(\"ping -c 3 \" + ip);\n}\n```",
        "good_code_patterns": "### Python - Parameterized Database Query\n```python\ndef get_user_data(username):\n    # SECURE: Parameters are sent separately from the command structure\n    query = \"SELECT * FROM users WHERE username = :username\"\n    return db.execute(query, {\"username\": username})\n```\n\n### Java - Safe System Execution\n```java\npublic void executePing(String ip) throws IOException {\n    // SECURE: Command and arguments are strictly separated\n    ProcessBuilder pb = new ProcessBuilder(\"ping\", \"-c\", \"3\", ip);\n    pb.start();\n}\n```",
        "common_mistakes": "1. Attempting to sanitize input by blacklisting certain characters (e.g., removing `'` or `;`), which is bypassable.\n2. Using ORMs but executing raw queries using string concatenation inside the ORM context.\n3. Relying on database triggers or stored procedures to prevent SQL injection without checking parameterization.",
        "secure_alternatives": "1. Use parameterized APIs, prepared statements, or Object-Relational Mappers (ORMs) exclusively.\n2. Validate inputs using strict allowlists (regex for known clean formats).\n3. Run database connections with least privilege, restricting write/execute capabilities.",
        "framework_notes": "SQLAlchemy automatically parameterizes queries when using `.filter()` or `.where()`. In Spring Data JPA, parameterize using method naming conventions or `@Query(\"SELECT u FROM User u WHERE u.username = :username\")`.",
        "performance_considerations": "Parameterized queries enable database engines to reuse execution plans, reducing CPU overhead and memory footprint on the database server.",
        "related_standards": "ASVS V5 (Validation, Sanitization and Encoding), PCI-DSS Requirement 6.5.1 (Injection vulnerabilities).",
        "references": "1. OWASP Top 10 A03: https://owasp.org/Top10/A03_2021-Injection/\n2. OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
    },
    "A04": {
        "title": "Insecure Design",
        "severity": "high",
        "priority": "high",
        "tags": ["design", "architecture", "threat-modeling", "defense-in-depth"],
        "source_url": "https://owasp.org/Top10/A04_2021-Insecure_Design/",
        "cwes": ["CWE-269", "CWE-601", "CWE-657", "CWE-1173"],
        "overview": "Insecure Design represents flaws in architecture and system design rather than implementation bugs. It focuses on the lack of threat modeling, secure design principles, and integration of security controls throughout the entire software lifecycle.",
        "why_it_matters": "No amount of secure coding can fix a fundamentally insecure design. Flawed designs allow attackers to abuse business logic, bypass authentication, or exploit weak system flows.",
        "detection_rules": "1. Review architectural diagrams and threat models to assess logical flaws.\n2. Evaluate design specifications for single points of failure or lack of defense-in-depth.\n3. Review business logic flows (e.g. registration, password reset) for logical bypasses.\n4. Audit privilege models and segregation of duties.",
        "bad_code_patterns": "### Python - Insecure Password Reset Logic\n```python\ndef reset_password(username, security_answer):\n    # VULNERABLE: Lacks rate limiting and account lockout. Answers are easily brute-forced.\n    user = db.get_user(username)\n    if user.answer == security_answer:\n        return generate_reset_token(user)\n    return \"Incorrect answer\"\n```\n\n### Java - Hardcoded Privilege Mapping\n```java\npublic boolean checkAccess(String role, String resource) {\n    // VULNERABLE: Dynamic hardcoded map that is difficult to maintain and audit\n    if (role.equals(\"ADMIN\")) return true;\n    if (resource.startsWith(\"/public\")) return true;\n    return false;\n}\n```",
        "good_code_patterns": "### Python - Multi-step Secure Password Reset with Expiry\n```python\ndef request_password_reset(email):\n    # SECURE: Send a high-entropy, short-lived verification token via email\n    token = generate_secure_token()\n    save_token_with_expiry(email, token, expiry=15 * 60) # 15 mins\n    send_reset_email(email, token)\n    return \"If the email exists, a reset link has been sent.\"\n```\n\n### Java - Standard Authorization Framework\n```java\n@Configuration\n@EnableWebSecurity\npublic class SecurityConfig {\n    @Bean\n    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {\n        // SECURE: Centralized, audited, and declarative access control configuration\n        http.authorizeHttpRequests(auth -> auth\n            .requestMatchers(\"/public/**\").permitAll()\n            .requestMatchers(\"/admin/**\").hasRole(\"ADMIN\")\n            .anyRequest().authenticated()\n        );\n        return http.build();\n    }\n}\n```",
        "common_mistakes": "1. Storing security questions in plaintext or relying on questions that can be guessed using OSINT.\n2. Designing applications without error boundaries, leading to cascade failures.\n3. Assuming internal systems do not require authentication or authorization.",
        "secure_alternatives": "1. Implement threat modeling methodologies (e.g. STRIDE) during the design phase.\n2. Adhere to secure design principles: Least Privilege, Separation of Duties, Fail Securely, and Defense in Depth.\n3. Integrate automated security tests (SAST, SCA) early in the CI/CD pipeline.",
        "framework_notes": "Use established authorization frameworks like Spring Security or FastAPI Security dependencies rather than implementing custom credential check flows.",
        "performance_considerations": "Design rate-limiting policies at the API gateway layer (e.g. Nginx, Kong) to prevent resource exhaustion without burdening backend application instances.",
        "related_standards": "NIST SP 800-160 (Systems Security Engineering), ISO/IEC 27034 (Application Security).",
        "references": "1. OWASP Top 10 A04: https://owasp.org/Top10/A04_2021-Insecure_Design/\n2. OWASP Threat Modeling Project: https://owasp.org/www-community/Threat_Modeling"
    },
    "A05": {
        "title": "Security Misconfiguration",
        "severity": "high",
        "priority": "high",
        "tags": ["misconfiguration", "hardening", "headers", "defaults"],
        "source_url": "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
        "cwes": ["CWE-2", "CWE-16", "CWE-200", "CWE-611"],
        "overview": "Security Misconfiguration happens when security controls are poorly configured, left at default settings, or misaligned with best practices. This includes leaving debug modes active, exposing verbose error stack traces, and failing to configure secure HTTP headers.",
        "why_it_matters": "Misconfigurations allow attackers to gather system banners, stack traces, and internal URLs, providing blueprints of application architectures. Default credentials and open ports allow immediate unauthorized entry.",
        "detection_rules": "1. Inspect environment config files for active debug modes in production.\n2. Scan applications for missing security headers (e.g. CSP, HSTS, X-Content-Type-Options).\n3. Audit network security groups and container configurations to ensure only required ports are exposed.\n4. Check for default configurations in database and web server instances.",
        "bad_code_patterns": "### Python - Flask Debug Mode Enabled\n```python\nif __name__ == '__main__':\n    # VULNERABLE: Running Flask in debug mode in production exposes an interactive debugger console\n    app.run(debug=True, host='0.0.0.0')\n```\n\n### Java - Raw Error Page Exposure\n```xml\n<!-- VULNERABLE: web.xml allowing system stack traces to display on errors -->\n<error-page>\n    <exception-type>java.lang.Throwable</exception-type>\n    <location>/error.jsp</location> <!-- If error.jsp prints exception.printStackTrace() -->\n</error-page>\n```",
        "good_code_patterns": "### Python - Production Flask Configuration\n```python\nimport os\n\n# SECURE: Read environment type and disable debug mode in production\nENV = os.environ.get(\"APP_ENV\", \"production\")\nDEBUG_MODE = ENV == \"development\"\n\nif __name__ == '__main__':\n    app.run(debug=DEBUG_MODE, host='127.0.0.1')\n```\n\n### Java - Secure Spring Boot Error Controller\n```java\n@RestControllerAdvice\npublic class GlobalExceptionHandler {\n    @ExceptionHandler(Exception.class)\n    public ResponseEntity<Map<String, String>> handleAllExceptions(Exception ex) {\n        // SECURE: Log internal stack trace locally, return generic message to client\n        logger.error(\"Exception occurred: \", ex);\n        Map<String, String> body = new HashMap<>();\n        body.put(\"error\", \"An internal error occurred. Please contact support.\");\n        return new ResponseEntity<>(body, HttpStatus.INTERNAL_SERVER_ERROR);\n    }\n}\n```",
        "common_mistakes": "1. Exposing database management panels (e.g. pgAdmin) or Swagger UI on public networks without authentication.\n2. Allowing permissive Cross-Origin Resource Sharing (CORS) headers (e.g. `Access-Control-Allow-Origin: *`) for authenticated endpoints.\n3. Using default database ports with default admin accounts (e.g. `postgres/postgres`).",
        "secure_alternatives": "1. Automated hardening scripts during system provisioning (e.g. Ansible, Terraform).\n2. Implement a strict Content Security Policy (CSP) and enforce HTTPS via HSTS headers.\n3. Regularly update configurations and check for defaults using automated configuration auditing tools.",
        "framework_notes": "FastAPI enables Swagger/Redoc docs by default. Disable `/docs` and `/redoc` routes in production. In Spring Boot, disable actuator endpoints or secure them behind role permissions.",
        "performance_considerations": "Configuring static security headers on the reverse proxy/CDN layer (e.g. Cloudflare, CloudFront) reduces load on application servers.",
        "related_standards": "ASVS V14 (Configuration Security), CIS Benchmarks, NIST SP 800-123 (Securing Public Web Servers).",
        "references": "1. OWASP Top 10 A05: https://owasp.org/Top10/A05_2021-Security_Misconfiguration/\n2. OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/"
    },
    "A06": {
        "title": "Vulnerable and Outdated Components",
        "severity": "high",
        "priority": "medium",
        "tags": ["dependencies", "sca", "patches", "vulnerable-libraries"],
        "source_url": "https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/",
        "cwes": ["CWE-937", "CWE-1035", "CWE-1104"],
        "overview": "This vulnerability involves using third-party components (libraries, packages, dependencies, OS packages) that contain known security issues (CVEs). It arises from a lack of dependency inventories and outdated patching workflows.",
        "why_it_matters": "Attackers continuously scan for public exploits of third-party libraries (e.g., Log4Shell, Apache Struts exploits). Relying on an outdated component allows attackers to run unauthorized commands, steal information, or compromise backend hosts.",
        "detection_rules": "1. Generate a Software Bill of Materials (SBOM) for the application.\n2. Use Software Composition Analysis (SCA) tools to verify all dependencies against vulnerability databases (CVE/NVD).\n3. Keep track of all third-party systems, frameworks, and web server software versions.\n4. Run tools like `pip-audit` for Python or `mvn dependency-check` for Maven in the CI/CD pipeline.",
        "bad_code_patterns": "### Python - Unlocked Dependencies in requirements.txt\n```text\n# VULNERABLE: No version pinning. Builds can pull highly outdated, insecure dependencies.\nrequests\nfastapi\nsqlalchemy\n```\n\n### Java - Insecure Log4j Dependency\n```xml\n<!-- VULNERABLE: Using version with Log4Shell (CVE-2021-44228) -->\n<dependency>\n    <groupId>org.apache.logging.log4j</groupId>\n    <artifactId>log4j-core</artifactId>\n    <version>2.14.1</version>\n</dependency>\n```",
        "good_code_patterns": "### Python - Pinned Dependencies with Hashes\n```text\n# SECURE: Version pinned and verified with cryptographic hashes\nrequests==2.31.0 --hash=sha256:58cd2187c3e888b5e9e037f6913551d34e56d405b8e97a78e7f1e7d801646253\nfastapi==0.100.0 --hash=sha256:0d2a8a816c729fca1a868bb27d49ee417c80521e42845344ad1401f8d48508eb\n```\n\n### Java - Upgraded Log4j Dependency\n```xml\n<!-- SECURE: Upgraded to safe, patched version -->\n<dependency>\n    <groupId>org.apache.logging.log4j</groupId>\n    <artifactId>log4j-core</artifactId>\n    <version>2.17.1</version>\n</dependency>\n```",
        "common_mistakes": "1. Importing libraries from untrusted sources or public repositories without verification.\n2. Leaving dependencies unmonitored for years without applying security patches.\n3. Failing to remove unused dependencies from the project configuration, increasing the attack surface.",
        "secure_alternatives": "1. Implement automated dependency checkers (e.g. Dependabot, Snyk, pip-audit).\n2. Build a policy that mandates patching critical dependencies within a strict window (e.g. 7 days from release).\n3. Keep a complete, dynamic inventory of all third-party libraries.",
        "framework_notes": "Use virtual environments (`venv`, `poetry`) in Python to isolate and manage dependencies. In Maven or Gradle, use dependency locking mechanisms.",
        "performance_considerations": "Minimizing dependencies reduces package size, improves cold start times (especially in serverless functions), and reduces memory overhead.",
        "related_standards": "ASVS V14.2 (Dependency Management), NIST SP 800-161 (Supply Chain Risk Management).",
        "references": "1. OWASP Top 10 A06: https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/\n2. OWASP Vulnerable Component Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Vulnerable_and_Outdated_Components_Cheat_Sheet.html"
    },
    "A07": {
        "title": "Identification and Authentication Failures",
        "severity": "critical",
        "priority": "high",
        "tags": ["authentication", "passwords", "session-management", "mfa"],
        "source_url": "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
        "cwes": ["CWE-287", "CWE-307", "CWE-340", "CWE-384"],
        "overview": "Identification and Authentication Failures occur when applications fail to confirm a user's identity, allowing attackers to hijack sessions, perform credential stuffing, or brute force their way into user accounts.",
        "why_it_matters": "Weaknesses in authentication bypass security perimeter defenses, allowing attackers to assume arbitrary identities, view proprietary information, and modify settings.",
        "detection_rules": "1. Check for lack of brute-force protection (no rate limits, account lockouts).\n2. Review password policies for weak complexity requirements.\n3. Verify session identifiers are refreshed upon login and properly invalidated on logout.\n4. Check if Multi-Factor Authentication (MFA) is absent for administrative portals.",
        "bad_code_patterns": "### Python - Simple Auth & Insecure Session ID\n```python\n@app.route('/login', methods=['POST'])\ndef login():\n    username = request.json.get('username')\n    password = request.json.get('password')\n    # VULNERABLE: Direct match without hashing (A02) and no login rate limit\n    user = db.get_user(username)\n    if user.password == password:\n        # VULNERABLE: Reusable session cookie with no secure attributes\n        resp = make_response(redirect('/dashboard'))\n        resp.set_cookie('session_id', user.username)\n        return resp\n```\n\n### Java - Session Fixation Vulnerability\n```java\npublic void authenticateUser(HttpServletRequest request, String username) {\n    // VULNERABLE: Authenticating user without regenerating session ID, allowing session fixation\n    HttpSession session = request.getSession(false);\n    if (session != null) {\n        session.setAttribute(\"user\", username);\n    }\n}\n```",
        "good_code_patterns": "### Python - Secure Password Check & Session Regeneration\n```python\nfrom werkzeug.security import check_password_hash\nfrom flask import session\n\n@app.route('/login', methods=['POST'])\n@limiter.limit(\"5 per minute\") # SECURE: Apply rate limit to prevent brute force\ndef login():\n    username = request.json.get('username')\n    password = request.json.get('password')\n    user = db.get_user(username)\n    if user and check_password_hash(user.password_hash, password):\n        # SECURE: Regenerate session id to prevent fixation\n        session.clear()\n        session['user_id'] = user.id\n        return jsonify({\"status\": \"success\"})\n    return jsonify({\"status\": \"unauthorized\"}), 401\n```\n\n### Java - Session Regeneration\n```java\npublic void authenticateUser(HttpServletRequest request, String username) {\n    // SECURE: Invalidating current session and creating a new one to regenerate session ID\n    request.getSession().invalidate();\n    HttpSession newSession = request.getSession(true);\n    newSession.setAttribute(\"user\", username);\n}\n```",
        "common_mistakes": "1. Allowing weak passwords (e.g. `123456`, `password`).\n2. Exposing session tokens in URLs (e.g. `http://site.com/dashboard?session_id=XYZ`).\n3. Failing to invalidate session tokens on the server when a user logs out.",
        "secure_alternatives": "1. Implement multi-factor authentication (MFA) everywhere.\n2. Implement a strict password complexity standard checked against a database of compromised passwords (HIBP).\n3. Set secure cookie flags: HttpOnly, Secure, and SameSite=Strict.",
        "framework_notes": "Use libraries like Flask-Login or Spring Security which handle session lifecycle management, CSRF validation, and session fixation protection automatically.",
        "performance_considerations": "MFA and password hashing are computation-heavy. Utilize dedicated caching layers for active sessions to prevent database degradation.",
        "related_standards": "ASVS V2 (Authentication), NIST SP 800-63B (Digital Identity Guidelines).",
        "references": "1. OWASP Top 10 A07: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/\n2. OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"
    },
    "A08": {
        "title": "Software and Data Integrity Failures",
        "severity": "high",
        "priority": "high",
        "tags": ["integrity", "deserialization", "ci-cd", "signatures"],
        "source_url": "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
        "cwes": ["CWE-502", "CWE-494", "CWE-829"],
        "overview": "This vulnerability occurs when code and infrastructure make assumptions about software updates, critical data, or CI/CD pipelines without verifying their integrity. A classic example is insecure deserialization, where untrusted data is converted into objects without verification.",
        "why_it_matters": "Attackers can intercept pipeline updates or manipulate serialized object streams to execute arbitrary code (RCE), tamper with data state, or bypass access controls.",
        "detection_rules": "1. Search code for usage of insecure deserialization functions (e.g. `pickle` in Python, native `ObjectInputStream` in Java).\n2. Review CI/CD configurations to verify dependencies and images are verified using signatures/hashes.\n3. Audit message queues (e.g. RabbitMQ) for payload validation.",
        "bad_code_patterns": "### Python - Insecure Deserialization (pickle)\n```python\nimport pickle\n\ndef load_user_session(cookie_data):\n    # VULNERABLE: Direct deserialization of user-provided data allows arbitrary code execution\n    return pickle.loads(cookie_data)\n```\n\n### Java - Insecure Deserialization\n```java\nimport java.io.ObjectInputStream;\nimport java.io.InputStream;\n\npublic class SessionLoader {\n    public Object deserialize(InputStream is) throws Exception {\n        // VULNERABLE: Restoring objects from untrusted streams allows RCE\n        ObjectInputStream ois = new ObjectInputStream(is);\n        return ois.readObject();\n    }\n}\n```",
        "good_code_patterns": "### Python - Safe Serialization (JSON)\n```python\nimport json\n\ndef load_user_session(cookie_data):\n    # SECURE: Parse only primitive data structures using JSON, avoiding code execution risks\n    return json.loads(cookie_data)\n```\n\n### Java - Safe Jackson JSON Parsing\n```java\nimport com.fasterxml.jackson.databind.ObjectMapper;\n\npublic class SessionLoader {\n    private ObjectMapper mapper = new ObjectMapper();\n    \n    public UserSession deserialize(String json) throws Exception {\n        // SECURE: Strictly maps input to a typed class structure without executing binary streams\n        return mapper.readValue(json, UserSession.class);\n    }\n}\n```",
        "common_mistakes": "1. Deserializing user-provided binary arrays, files, or cookies using raw serialization features of programming languages.\n2. Pushing software updates or docker base images without validating their checksums or signatures.\n3. Using unsigned JSON Web Tokens (JWT) where the server accepts the `none` algorithm.",
        "secure_alternatives": "1. Use standardized data serialization formats (like JSON, YAML, Protocol Buffers) that don't allow arbitrary code execution.\n2. Cryptographically sign serialized payloads using HMAC or asymmetric keys before transmission.\n3. Implement software signing pipelines and verify components using SCA.",
        "framework_notes": "Avoid native Java serialization at all costs. In Python, replace `pickle` or `marshal` with `pydantic` and JSON parsing.",
        "performance_considerations": "JSON/Protocol Buffers parsing is significantly faster and less memory-intensive than Java object serialization or Python's pickle parser.",
        "related_standards": "ASVS V10 (Malicious Code), NIST SP 800-161 (Supply Chain Security).",
        "references": "1. OWASP Top 10 A08: https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/\n2. OWASP Deserialization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html"
    },
    "A09": {
        "title": "Security Logging and Monitoring Failures",
        "severity": "medium",
        "priority": "medium",
        "tags": ["logging", "monitoring", "audit-logs", "siem"],
        "source_url": "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/",
        "cwes": ["CWE-117", "CWE-778", "CWE-779"],
        "overview": "Security Logging and Monitoring Failures occur when applications do not log security-critical events (failed logins, privilege changes), or when logs are not actively monitored. This prevents detection, tracking, and timely containment of active security breaches.",
        "why_it_matters": "Without proper logging and monitoring, attackers can maintain persistent access for months before detection. It also prevents forensic analysis during post-incident investigations.",
        "detection_rules": "1. Check if security-critical actions (logins, authorization failures, data updates) fail to generate logs.\n2. Inspect logs for presence of sensitive data (passwords, session keys, credit card numbers).\n3. Audit alerts and monitoring tools to ensure threshold violations trigger notifications.\n4. Check if logs are stored strictly locally without centralization.",
        "bad_code_patterns": "### Python - Log Injection Vulnerability\n```python\nimport logging\n\ndef process_login(username):\n    # VULNERABLE: Writing unvalidated user input directly into logs (Log Injection/Forging)\n    logging.info(f\"User {username} attempted login\")\n```\n\n### Java - Omission of Security Event Logging\n```java\npublic boolean loginUser(String user, String pass) {\n    boolean authenticated = authService.check(user, pass);\n    if (!authenticated) {\n        // VULNERABLE: Failed authentication attempts are not logged, blinding administrators to brute force\n        return false;\n    }\n    return true;\n}\n```",
        "good_code_patterns": "### Python - Safe Structured Logging\n```python\nimport logging\nimport json\n\ndef process_login(username):\n    # SECURE: Sanitize input by replacing line breaks, or structure as JSON to prevent forging\n    sanitized_user = username.replace('\\n', '').replace('\\r', '')\n    log_payload = {\"event\": \"login_attempt\", \"user\": sanitized_user}\n    logging.info(json.dumps(log_payload))\n```\n\n### Java - Structured Audit Logging\n```java\nprivate static final Logger logger = LoggerFactory.getLogger(LoginController.class);\n\npublic boolean loginUser(String user, String pass, String clientIp) {\n    boolean authenticated = authService.check(user, pass);\n    if (!authenticated) {\n        // SECURE: Log failed authentication with context details (excluding credentials)\n        logger.warn(\"SECURITY: Failed login attempt for user={}, ip={}\", user, clientIp);\n        return false;\n    }\n    return true;\n}\n```",
        "common_mistakes": "1. Logging plaintext passwords or PII (e.g. social security numbers, credit card tokens).\n2. Writing logs to local files without shipping them to a secure, centralized log management platform (SIEM).\n3. Setting log levels too high (e.g., only logging `FATAL` errors), missing critical security warnings (`WARN`).",
        "secure_alternatives": "1. Standardize logging formats using JSON to facilitate automated ingestion by SIEM tools (e.g., Splunk, ELK).\n2. Establish real-time alerts for critical events like administrative role changes or multiple failed logins.\n3. Implement write-only/append-only storage for security logs.",
        "framework_notes": "Use structlog in Python or Logback with logstash-logback-encoder in Spring Boot for clean, structured JSON logging.",
        "performance_considerations": "Perform logging asynchronously using queues (e.g. Logback's `AsyncAppender`) to avoid blocking request threads during disk write operations.",
        "related_standards": "ASVS V7.4 (Security Logging), ISO 27001 A.12.4 (Logging and Monitoring).",
        "references": "1. OWASP Top 10 A09: https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/\n2. OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html"
    },
    "A10": {
        "title": "Server-Side Request Forgery",
        "severity": "high",
        "priority": "high",
        "tags": ["ssrf", "network-security", "url-validation", "allowlist"],
        "source_url": "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/",
        "cwes": ["CWE-918"],
        "overview": "Server-Side Request Forgery (SSRF) occurs when a web application fetches a remote resource from a user-supplied URL without validating the address. This allows attackers to force the server to send HTTP/TCP requests to internal resources, metadata endpoints, or third-party APIs.",
        "why_it_matters": "SSRF can be leveraged to scan internal private ports, bypass firewall controls, and access cloud metadata services (e.g., AWS IMDSv1/v2 at `169.254.169.254`), exposing IAM keys and database credentials.",
        "detection_rules": "1. Audit endpoints that accept URLs as parameters (e.g., file upload from link, webhook setup).\n2. Test using DNS tracking services (e.g., Interactsh) to confirm out-of-band network calls.\n3. Check if server allows requests to loopback addresses (`127.0.0.1`, `localhost`) or private network ranges.",
        "bad_code_patterns": "### Python - Arbitrary URL Fetch\n```python\nimport requests\n\n@app.route('/fetch-image')\ndef fetch_image():\n    url = request.args.get('url')\n    # VULNERABLE: Directly fetching user-supplied URL allows SSRF\n    r = requests.get(url)\n    return r.content\n```\n\n### Java - Raw HTTP Connection\n```java\npublic void retrieveData(String targetUrl) throws Exception {\n    // VULNERABLE: Direct connection to arbitrary user input URL\n    URL url = new URL(targetUrl);\n    HttpURLConnection conn = (HttpURLConnection) url.openConnection();\n    conn.setRequestMethod(\"GET\");\n    conn.getInputStream().read();\n}\n```",
        "good_code_patterns": "### Python - Strict URL Allowlist\n```python\nfrom urllib.parse import urlparse\nimport requests\n\nALLOWED_DOMAINS = [\"trusted-domain.com\", \"images.trusted.com\"]\n\n@app.route('/fetch-image')\ndef fetch_image():\n    url = request.args.get('url')\n    parsed_url = urlparse(url)\n    # SECURE: Restrict scheme to HTTPS and restrict domain name to allowlist\n    if parsed_url.scheme != 'https' or parsed_url.netloc not in ALLOWED_DOMAINS:\n        return \"Invalid URL\", 400\n    r = requests.get(url)\n    return r.content\n```\n\n### Java - Safe Socket Verification\n```java\npublic void retrieveData(String targetUrl) throws Exception {\n    URL url = new URL(targetUrl);\n    String host = url.getHost();\n    // SECURE: Resolve DNS and check against local subnet ranges\n    InetAddress address = InetAddress.getByName(host);\n    if (address.isLoopbackAddress() || address.isSiteLocalAddress()) {\n        throw new IllegalArgumentException(\"Requests to internal IP ranges are forbidden\");\n    }\n    HttpURLConnection conn = (HttpURLConnection) url.openConnection();\n    // proceed...\n}\n```",
        "common_mistakes": "1. Implementing blacklist validation filters (e.g., blocking `127.0.0.1` but failing to block decimal equivalents like `2130706433` or DNS redirects).\n2. Permitting arbitrary protocols (e.g. `file://`, `gopher://`, `ftp://`) which can lead to file disclosure.",
        "secure_alternatives": "1. Implement a strict allowlist of domains and URL schemes.\n2. Isolate network-facing microservices within a separate sandbox, denying access to cloud metadata services.\n3. Resolve target domains to IPs and check them against RFC1918 private ranges prior to making requests.",
        "framework_notes": "Always use a specialized client that disables HTTP redirects or limit the maximum redirects to prevent redirect-based SSRF bypasses.",
        "performance_considerations": "Use timeouts on outbound HTTP requests to prevent attackers from causing denial-of-service by submitting targets that delay responses.",
        "related_standards": "ASVS V5.2 (Sanitization and Input Validation), NIST SP 800-53 SC-7 (Boundary Protection).",
        "references": "1. OWASP Top 10 A10: https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/\n2. OWASP SSRF Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
    }
}

# API Security Top 10 data
API_DATA = {
    "API1": {
        "title": "Broken Object Level Authorization",
        "overview": "Broken Object Level Authorization (BOLA) occurs when an application exposes endpoints that access objects by ID but fails to validate that the requester has permissions to access those specific objects.",
        "why_it_matters": "BOLA allows attackers to easily harvest or modify other users' sensitive information by enumerating identifiers in URL parameters or request bodies (e.g., changing `/api/v1/user/1001` to `/api/v1/user/1002`).",
        "detection_rules": "1. Check if ID parameters can be manipulated to access records belonging to other accounts.\n2. Use SAST to verify that access control checks check object-level owner attributes against user ID context.",
        "bad_code": "```python\n@app.get('/api/orders/{order_id}')\ndef get_order(order_id: int):\n    # VULNERABLE: Loads order directly without validating ownership\n    return db.query_order(order_id)\n```",
        "good_code": "```python\n@app.get('/api/orders/{order_id}')\ndef get_order(order_id: int, current_user = Depends(get_current_user)):\n    order = db.query_order(order_id)\n    # SECURE: Validate ownership before returning object\n    if order.user_id != current_user.id:\n        raise HTTPException(status_code=403, detail=\"Access denied\")\n    return order\n```",
        "common_mistakes": "Relying on client-provided ownership flags or assuming that checking login authentication is sufficient to protect specific records.",
        "secure_alternatives": "Use randomized UUIDs for resource identifiers and implement authorization filters checking access tokens against resource owner mappings in the database.",
        "framework_notes": "Use custom FastAPI decorators or Spring Boot interceptors to load objects and perform authorization checks before handler methods execute.",
        "performance": "Index owner relationship fields in database tables to keep ownership lookups fast.",
        "related": "CWE-639 (Insecure Direct Object Reference), OWASP Top 10 A01",
        "references": "OWASP API Security Top 10: API1:2023"
    },
    "API2": {
        "title": "Broken Authentication",
        "overview": "Broken Authentication in APIs refers to weaknesses in authentication flows, tokens (JWT), or session management that allow attackers to assume other users' identities.",
        "why_it_matters": "Compromised authentication permits unauthorized API execution, leading to data theft, modification, and execution of sensitive admin actions.",
        "detection_rules": "1. Review JWT configurations for weak verification keys or usage of the 'none' algorithm.\n2. Test API endpoints for credential-stuffing vulnerability (lack of rate-limiting).",
        "bad_code": "```python\n# VULNERABLE: Accepting JWT without cryptographic signature verification\ndef verify_token(token):\n    payload = jwt.decode(token, options={\"verify_signature\": False})\n    return payload\n```",
        "good_code": "```python\n# SECURE: Enforce signature verification and expiration check\ndef verify_token(token):\n    try:\n        return jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])\n    except jwt.ExpiredSignatureError:\n        raise HTTPException(status_code=401, detail=\"Token expired\")\n```",
        "common_mistakes": "Exposing API keys in git repositories or sending session tokens as query parameters.",
        "secure_alternatives": "Enforce Multi-Factor Authentication (MFA), use OAuth2 token verification, and rotate signature keys regularly.",
        "framework_notes": "Use Spring Security OAuth2 Resource Server or FastAPI oauth2 schemes to handle JWT verification.",
        "performance": "Cache signature verification public keys to avoid fetching them from the JWKS provider on every request.",
        "related": "CWE-287, OWASP Top 10 A07",
        "references": "OWASP API Security Top 10: API2:2023"
    },
    "API3": {
        "title": "Broken Object Property Level Authorization",
        "overview": "Broken Object Property Level Authorization (BOPLA) occurs when APIs expose properties of objects that should remain hidden, or allow modifying fields they shouldn't.",
        "why_it_matters": "Attackers can intercept sensitive information (e.g. password hash or SSN returned in JSON) or overwrite fields like account roles by submitting unauthorized payload parameters.",
        "detection_rules": "1. Verify endpoints return only requested/allowed fields.\n2. Attempt mass assignment by sending additional JSON properties (e.g. `\"is_admin\": true`).",
        "bad_code": "```python\n# VULNERABLE: Direct model update allows mass assignment\n@app.put('/api/profile')\ndef update_profile(data: dict, current_user = Depends(get_user)):\n    db.update_user(current_user.id, **data)\n```",
        "good_code": "```python\n# SECURE: Use strict schema validators (Pydantic) to limit modifiable fields\nclass ProfileUpdate(BaseModel):\n    bio: str\n    display_name: str\n\n@app.put('/api/profile')\ndef update_profile(data: ProfileUpdate, current_user = Depends(get_user)):\n    db.update_user(current_user.id, bio=data.bio, display_name=data.display_name)\n```",
        "common_mistakes": "Returning raw domain entities to the client instead of Data Transfer Objects (DTO).",
        "secure_alternatives": "Use DTOs or Pydantic models to strictly define response and request serialization schemas.",
        "framework_notes": "In FastAPI, leverage `response_model` to automatically filter response data.",
        "performance": "Querying only required columns from the database (e.g., avoiding `SELECT *`) improves database performance.",
        "related": "CWE-915 (Mass Assignment), OWASP Top 10 A01",
        "references": "OWASP API Security Top 10: API3:2023"
    },
    "API4": {
        "title": "Unrestricted Resource Consumption",
        "overview": "Unrestricted Resource Consumption occurs when APIs fail to limit request volumes, file sizes, or resource usage, causing service degradation or complete denial of service.",
        "why_it_matters": "Attackers can exploit this to overwhelm servers, exhaust system memory, run up cloud infrastructure costs, or crash databases.",
        "detection_rules": "1. Verify APIs limit size of uploaded files.\n2. Verify rate-limiting is active on all public endpoints.",
        "bad_code": "```python\n# VULNERABLE: Fetching unbounded pages from database\n@app.get('/api/users')\ndef list_users(limit: int):\n    return db.query(\"SELECT * FROM users LIMIT %s\", limit)\n```",
        "good_code": "```python\n# SECURE: Hard limit the maximum page size\n@app.get('/api/users')\ndef list_users(limit: int = 20):\n    safe_limit = min(limit, 100)\n    return db.query(\"SELECT * FROM users LIMIT %s\", safe_limit)\n```",
        "common_mistakes": "Failing to set timeouts on network requests and database queries.",
        "secure_alternatives": "Deploy rate-limiters at the gateway level, enforce strict payload limits, and implement pagination.",
        "framework_notes": "Use ASGI rate limiters in FastAPI or bucket4j in Spring Boot.",
        "performance": "Set memory and cpu limits on container runtimes to prevent a single service from crashing the host.",
        "related": "CWE-770, OWASP Top 10 A05",
        "references": "OWASP API Security Top 10: API4:2023"
    },
    "API5": {
        "title": "Broken Function Level Authorization",
        "overview": "Broken Function Level Authorization (BFLA) happens when authorization policies are missing or incorrectly implemented for specific API routes (especially administrative or management functions).",
        "why_it_matters": "Attackers can guess admin URL patterns (e.g., swapping `/api/v1/users/` for `/api/v1/admin/users/`) and execute restricted functions (such as deletion or configurations).",
        "detection_rules": "1. Attempt calling admin endpoints with low-privilege tokens.\n2. Review routing paths and verify middleware check functions.",
        "bad_code": "```python\n# VULNERABLE: No role check validation\n@app.delete('/api/admin/users/{user_id}')\ndef delete_user(user_id: int):\n    db.delete(user_id)\n```",
        "good_code": "```python\n# SECURE: Enforce admin role dependency\n@app.delete('/api/admin/users/{user_id}', dependencies=[Depends(require_admin_role)])\ndef delete_user(user_id: int):\n    db.delete(user_id)\n```",
        "common_mistakes": "Obfuscating URLs instead of implementing robust server-side access controls.",
        "secure_alternatives": "Implement role-based or attribute-based access control policies at every API interface.",
        "framework_notes": "Use Spring Security WebSecurityConfigurerAdapter or FastAPI route dependencies.",
        "performance": "Use cached user role lists to prevent double-queries during authorization.",
        "related": "CWE-285, OWASP Top 10 A01",
        "references": "OWASP API Security Top 10: API5:2023"
    },
    "API6": {
        "title": "Unrestricted Access to Sensitive Business Flows",
        "overview": "This vulnerability occurs when APIs expose business logic flows (like account creation, purchasing, booking) without considering automated exploitation or excessive usage.",
        "why_it_matters": "Bots can script actions to buy up limited inventory, scrape pricing, or spam account registration systems.",
        "detection_rules": "1. Check if endpoints lack rate limiting or CAPTCHA validation.\n2. Verify system cannot identify automated user agent patterns.",
        "bad_code": "```python\n# VULNERABLE: Simple submission route with no bot checks\n@app.post('/api/ticket/purchase')\ndef buy_ticket(ticket_id: int):\n    return transaction_service.process(ticket_id)\n```",
        "good_code": "```python\n# SECURE: Require CAPTCHA validation token and apply strict ip rate limits\n@app.post('/api/ticket/purchase')\n@limiter.limit(\"2 per minute\")\ndef buy_ticket(ticket_id: int, captcha_token: str = Header(...)):\n    verify_captcha(captcha_token)\n    return transaction_service.process(ticket_id)\n```",
        "common_mistakes": "Assuming simple authorization rules are sufficient to stop bot nets.",
        "secure_alternatives": "Integrate device fingerprinting, CAPTCHA solutions, and threshold monitors.",
        "framework_notes": "Configure WAF (Web Application Firewall) policies to detect headless browser fingerprints.",
        "performance": "Differentiate static requests from transaction API calls to selectively apply heavy bot defenses.",
        "related": "CWE-799, OWASP Top 10 A04",
        "references": "OWASP API Security Top 10: API6:2023"
    },
    "API7": {
        "title": "Server Side Request Forgery (SSRF)",
        "overview": "SSRF occurs when API endpoints fetch remote resources using user-submitted URLs without checking the target destination.",
        "why_it_matters": "Attackers force the API server to query internal subnets, local host services, or container metadata configurations.",
        "detection_rules": "Check if API endpoints accept external URLs and resolve them to internal IP segments.",
        "bad_code": "```python\n# VULNERABLE: Fetching raw url parameter\n@app.post('/api/fetch-logo')\ndef get_logo(url: str):\n    return requests.get(url).content\n```",
        "good_code": "```python\n# SECURE: Strict allowlist and scheme checks\n@app.post('/api/fetch-logo')\ndef get_logo(url: str):\n    parsed = urlparse(url)\n    if parsed.scheme != 'https' or parsed.netloc not in ALLOWED_DOMAINS:\n        raise HTTPException(400, \"Invalid URL\")\n    return requests.get(url).content\n```",
        "common_mistakes": "Relying on regex blacklists instead of domain allowlists.",
        "secure_alternatives": "Apply domain allowlists, resolve hostnames, and block private IP address ranges.",
        "framework_notes": "Configure internal firewall rules to deny outgoing traffic from container subnets to host metadata services.",
        "performance": "Set short request connect timeouts to prevent network socket starvation.",
        "related": "CWE-918, OWASP Top 10 A10",
        "references": "OWASP API Security Top 10: API7:2023"
    },
    "API8": {
        "title": "Security Misconfiguration",
        "overview": "Security Misconfiguration in APIs refers to exposed debug pages, verbose error messages, or insecure transport configurations.",
        "why_it_matters": "Attackers gain architectural descriptions, database types, or open connections to execute attacks directly.",
        "detection_rules": "Scan API paths for CORS allow-all headers, default error outputs, or unencrypted endpoints.",
        "bad_code": "```python\n# VULNERABLE: CORS allow-all and verbose logs\napp.add_middleware(CORSMiddleware, allow_origins=[\"*\"])\n```",
        "good_code": "```python\n# SECURE: Limit allowed origins to trusted domains\napp.add_middleware(CORSMiddleware, allow_origins=[\"https://app.domain.com\"])\n```",
        "common_mistakes": "Exposing dev/stage API documentation endpoints in production environments.",
        "secure_alternatives": "Build configuration profiles and perform regular environment scans.",
        "framework_notes": "Disable swagger endpoints on production profiles in FastAPI.",
        "performance": "Apply compression and CORS headers at the load balancer level.",
        "related": "CWE-16, OWASP Top 10 A05",
        "references": "OWASP API Security Top 10: API8:2023"
    },
    "API9": {
        "title": "Improper Assets Management",
        "overview": "Improper Assets Management is the exposure of deprecated, debug, or undocumented API versions (e.g., leaving `/api/v1/` active alongside `/api/v2/`).",
        "why_it_matters": "Attackers focus on older versions of API endpoints that lack recent access control improvements or security checks.",
        "detection_rules": "Map and index all active API routes. Look for undocumented paths.",
        "bad_code": "```python\n# VULNERABLE: Leaving insecure deprecated endpoints active without checks\n@app.get('/api/v1/user/debug')\ndef debug_users():\n    return db.get_raw_users()\n```",
        "good_code": "```python\n# SECURE: Delete deprecated debug endpoints or enforce admin-only checks\n@app.get('/api/v2/user/info', dependencies=[Depends(require_user)])\ndef get_user_info():\n    return db.get_safe_user_data()\n```",
        "common_mistakes": "Failing to document new API endpoints or neglecting decommissioning processes.",
        "secure_alternatives": "Create an API service register, apply API gateways, and delete old endpoints.",
        "framework_notes": "Maintain versioning schemes (e.g. prefix routes with `/api/v2/`).",
        "performance": "Routing legacy clients to specific deprecation notices reduces main server computation costs.",
        "related": "CWE-1059, OWASP Top 10 A06",
        "references": "OWASP API Security Top 10: API9:2023"
    },
    "API10": {
        "title": "Unsafe Consumption of APIs",
        "overview": "Unsafe Consumption of APIs happens when an application trusts data returned from third-party APIs without proper validation.",
        "why_it_matters": "If the third-party API is compromised, the host application will process malicious inputs, leading to SQLi, XSS, or RCE.",
        "detection_rules": "Audit external API client connections and trace incoming data objects through security validation layers.",
        "bad_code": "```python\n# VULNERABLE: Direct database insert of third-party API response data\ndef sync_weather():\n    data = requests.get('https://api.weather.com/data').json()\n    db.execute(f\"INSERT INTO status VALUES ('{data['status']}')\")\n```",
        "good_code": "```python\n# SECURE: Validate data format and use parameterized queries\ndef sync_weather():\n    data = requests.get('https://api.weather.com/data').json()\n    status_val = str(data.get('status', 'Unknown'))\n    # Use parameterized database write\n    db.execute(\"INSERT INTO status VALUES (:status)\", {\"status\": status_val})\n```",
        "common_mistakes": "Assuming data from trusted partners does not require filtering or sanitization.",
        "secure_alternatives": "Treat all third-party API payloads as untrusted input. Validate format, length, and content.",
        "framework_notes": "Use deserialization models (like Pydantic) to strictly check external API payloads.",
        "performance": "Isolate external API client threads to avoid third-party network delays blocking the rest of the application.",
        "related": "CWE-20, OWASP Top 10 A08",
        "references": "OWASP API Security Top 10: API10:2023"
    }
}

# Proactive Controls C1-C10 data
PROACTIVE_DATA = {
    "C1": {
        "title": "Implement Access Control",
        "overview": "Define and enforce access permissions for objects and operations. Deny by default.",
        "why_it_matters": "Access control forms the primary barrier preventing unauthorized access and privilege escalation.",
        "detection_rules": "Confirm that all application routes are protected by access rules. Run permission validation checks.",
        "bad_code": "```python\n# VULNERABLE: Route exposes operation without check\ndef delete_item(item_id):\n    db.delete(item_id)\n```",
        "good_code": "```python\n# SECURE: Route validates permissions and context\n@require_permission('delete_items')\ndef delete_item(item_id, user):\n    db.delete_item(item_id, user.id)\n```",
        "common_mistakes": "Relying on URL-based protection only. Forgetting to validate access on individual object instances.",
        "secure_alternatives": "Use Role-Based (RBAC) or Attribute-Based Access Control (ABAC) models.",
        "framework_notes": "Implement global authentication guards.",
        "performance": "Cache access decision rules to speed up request authorization.",
        "related": "CWE-285, OWASP A01",
        "references": "OWASP Proactive Controls C1"
    },
    "C2": {
        "title": "Use Cryptography the Proper Way",
        "overview": "Protect sensitive data using strong cryptographic algorithms and proper key management.",
        "why_it_matters": "Compromised keys or weak algorithms allow decryption of passwords, credentials, and data.",
        "detection_rules": "Scan code for weak algorithms (MD5, DES) and verify secret management policies.",
        "bad_code": "```python\n# VULNERABLE: Hardcoded weak encryption key\ncipher = AES.new('weakkey123456789', AES.MODE_ECB)\n```",
        "good_code": "```python\n# SECURE: High-entropy key loaded from environment and secure mode GCM\ncipher = AES.new(os.environ['AES_KEY'], AES.MODE_GCM, nonce=nonce)\n```",
        "common_mistakes": "Creating proprietary cryptographic formulas or reusing salts/nonces.",
        "secure_alternatives": "Use Standard Cryptographic Libraries (e.g. PyCryptodome, JCA) and KMS (Key Management Services).",
        "framework_notes": "Leverage framework configuration parameters for secure hash settings.",
        "performance": "Prefer AES-GCM for hardware-accelerated decryption efficiency.",
        "related": "CWE-327, OWASP A02",
        "references": "OWASP Proactive Controls C2"
    },
    "C3": {
        "title": "Validate all Input and Handle Exceptions",
        "overview": "Sanitize and validate all incoming data fields before processing or storing them, and ensure errors do not disclose system details.",
        "why_it_matters": "Invalid input causes injection, cross-site scripting, and application crashes. Raw exceptions expose configuration blueprints.",
        "detection_rules": "Examine input controllers for validator integrations. Check exception handlers for raw stack trace outputs.",
        "bad_code": "```python\n# VULNERABLE: Direct access to payload parameters\ndef process_age(req):\n    return int(req.params.get('age'))\n```",
        "good_code": "```python\n# SECURE: Strict validation range check and type coercion\ndef process_age(req):\n    age_raw = req.params.get('age')\n    if not age_raw.isdigit():\n        raise ValueError(\"Invalid format\")\n    age = int(age_raw)\n    if age < 0 or age > 120:\n        raise ValueError(\"Invalid range\")\n    return age\n```",
        "common_mistakes": "Relying strictly client side or trying to construct blacklist filters.",
        "secure_alternatives": "Apply schema-based validation libraries (Pydantic, Hibernate Validator) and write centralized error handlers.",
        "framework_notes": "FastAPI does type and validation using Pydantic parameters automatically.",
        "performance": "Keep validation steps lightweight. Cache complex regex compilation patterns.",
        "related": "CWE-20, OWASP A03",
        "references": "OWASP Proactive Controls C3"
    },
    "C4": {
        "title": "Address Security from the Start",
        "overview": "Incorporate security design guidelines, threat modeling, and testing into the early stages of software development lifecycle (SDLC).",
        "why_it_matters": "Design defects are extremely expensive to remediate if detected in production.",
        "detection_rules": "Confirm threat modeling documents are created before coding features. Verify security tests run in CI.",
        "bad_code": "```text\n# VULNERABLE: Standard design document with zero mention of threat modeling or data privacy controls\n```",
        "good_code": "```text\n# SECURE: Design review includes a STRIDE threat map and security verification requirements\n```",
        "common_mistakes": "Treating security checks as a separate phase before deployment rather than a continuous cycle.",
        "secure_alternatives": "Adopt SSDLC (Secure Software Development Lifecycle) principles.",
        "framework_notes": "Use containerized checks and SAST linters inside pipeline scripts.",
        "performance": "Shift-left reduces development cycles by catching bugs before deployment.",
        "related": "CWE-1173, OWASP A04",
        "references": "OWASP Proactive Controls C4"
    },
    "C5": {
        "title": "Secure By Default Configurations",
        "overview": "Deliver applications and systems hardened, requiring explicit configuration changes to decrease security controls.",
        "why_it_matters": "Default accounts and loose transport privileges are the easiest entry points for scanners.",
        "detection_rules": "Scan setup scripts for default passwords, active admin accounts, or debug ports.",
        "bad_code": "```python\n# VULNERABLE: Default credentials and public database access\nDB_PASS = 'postgres'\nDB_HOST = '0.0.0.0'\n```",
        "good_code": "```python\n# SECURE: Enforced configuration overrides and localhost limits\nDB_PASS = os.environ['DB_PASSWORD']\nDB_HOST = '127.0.0.1'\n```",
        "common_mistakes": "Deploying default config files. Leaving sample pages active.",
        "secure_alternatives": "Enforce hardening policies using automated deployment environments.",
        "framework_notes": "Configure framework environments to production by default.",
        "performance": "Hardening server ports blocks background scan traffic, saving processing threads.",
        "related": "CWE-16, OWASP A05",
        "references": "OWASP Proactive Controls C5"
    },
    "C6": {
        "title": "Keep your Components Secure",
        "overview": "Maintain an inventory of libraries and check for patches to keep third-party components safe.",
        "why_it_matters": "Insecure dependencies allow attackers to bypass software defenses using public exploits.",
        "detection_rules": "Run dependency scanners to map components against CVE listings.",
        "bad_code": "```text\n# VULNERABLE: Using unpinned dependencies\nflask\n```",
        "good_code": "```text\n# SECURE: Pinned and hashed dependency configuration\nflask==3.0.0 --hash=sha256:...\n```",
        "common_mistakes": "Allowing libraries without checking vulnerability alerts.",
        "secure_alternatives": "Adopt automated patch mechanisms and Dependency Track tools.",
        "framework_notes": "Use locks (poetry.lock, package-lock.json).",
        "performance": "Removing unused modules reduces memory consumption and application startup time.",
        "related": "CWE-937, OWASP A06",
        "references": "OWASP Proactive Controls C6"
    },
    "C7": {
        "title": "Implement Digital Identity",
        "overview": "Implement secure authentication systems to confirm identity and safely coordinate sessions.",
        "why_it_matters": "Authentication failures allow session theft and credential bypasses.",
        "detection_rules": "Verify cookies possess HttpOnly, Secure, and SameSite parameters. Check brute force protections.",
        "bad_code": "```python\n# VULNERABLE: Insecure cookies\nresponse.set_cookie('session', user_id)\n```",
        "good_code": "```python\n# SECURE: Secure session cookie attributes\nresponse.set_cookie('session', session_id, httponly=True, secure=True, samesite='Strict')\n```",
        "common_mistakes": "Allowing weak passwords or exposing tokens in HTTP headers or URLs.",
        "secure_alternatives": "Implement Multi-Factor Authentication (MFA) and secure identity providers (SAML, OIDC).",
        "framework_notes": "Use Spring Security session controls or FastAPI Security dependencies.",
        "performance": "Utilize memory stores like Redis for rapid validation of active sessions.",
        "related": "CWE-287, OWASP A07",
        "references": "OWASP Proactive Controls C7"
    },
    "C8": {
        "title": "Leverage Browser Security Features",
        "overview": "Configure application responses with headers (CSP, HSTS) to direct browsers to apply built-in security features.",
        "why_it_matters": "Security headers block XSS, clickjacking, and packet sniffing attacks.",
        "detection_rules": "Examine response headers for security attributes.",
        "bad_code": "```python\n# VULNERABLE: Missing protection headers\n@app.get('/')\ndef index():\n    return \"Hello\"\n```",
        "good_code": "```python\n# SECURE: Add secure HTTP headers manually or via middleware\n@app.get('/')\ndef index(response: Response):\n    response.headers['Content-Security-Policy'] = \"default-src 'self'\"\n    response.headers['X-Frame-Options'] = 'DENY'\n    return \"Hello\"\n```",
        "common_mistakes": "Applying permissive Content Security Policies (e.g. allowing `unsafe-inline`).",
        "secure_alternatives": "Integrate secure headers plugins into reverse proxies (Nginx) or framework setups.",
        "framework_notes": "Use Spring Security's defaults, which add secure headers automatically.",
        "performance": "Configuring security headers at reverse proxies keeps backend response pipelines simple.",
        "related": "CWE-79, OWASP A05",
        "references": "OWASP Proactive Controls C8"
    },
    "C9": {
        "title": "Implement Security Logging and Monitoring",
        "overview": "Log security-critical operations in a structured format and monitor them to identify breaches.",
        "why_it_matters": "Inadequate monitoring keeps intrusions hidden, blocking investigations and incident containment.",
        "detection_rules": "Confirm failed login attempts and permission actions write entries to logs. Check for sensitive data.",
        "bad_code": "```python\n# VULNERABLE: Logging sensitive customer password data\nlogger.info(f\"User {username} logged in with pass {password}\")\n```",
        "good_code": "```python\n# SECURE: Structured JSON logs containing only metadata\nlogger.info(json.dumps({\"event\": \"auth_success\", \"user\": username, \"ip\": client_ip}))\n```",
        "common_mistakes": "Writing logs to local files without shipping them to centralized storage.",
        "secure_alternatives": "Deploy SIEM tools and structured JSON log pipelines.",
        "framework_notes": "Utilize logging configuration libraries (Logback, python-logging).",
        "performance": "Set logging activities to execute asynchronously to prevent locking main request threads.",
        "related": "CWE-778, OWASP A09",
        "references": "OWASP Proactive Controls C9"
    },
    "C10": {
        "title": "Stop Server Side Request Forgery",
        "overview": "Mitigate SSRF risk by validating schemes, allowlisting domains, and resolving DNS target addresses.",
        "why_it_matters": "Unrestricted requests allow scanning internal configurations and cloud databases.",
        "detection_rules": "Locate routes accepting URLs and evaluate validation checks.",
        "bad_code": "```python\n# VULNERABLE: Direct request to arbitrary host\nrequests.get(url)\n```",
        "good_code": "```python\n# SECURE: Verify scheme and restrict requests to domain allowlist\nparsed = urlparse(url)\nif parsed.scheme == 'https' and parsed.netloc in ALLOWED_DOMAINS:\n    requests.get(url)\n```",
        "common_mistakes": "Using blacklists or forgetting redirect handling.",
        "secure_alternatives": "Execute requests inside a separate VPC subnet without internal access.",
        "framework_notes": "Configure underlying network routers to drop local requests.",
        "performance": "Set connection and read timeouts on external API requests.",
        "related": "CWE-918, OWASP A10",
        "references": "OWASP Proactive Controls C10"
    }
}

# Selected Cheat Sheets data
CHEAT_DATA = {
    "sql_injection_prevention": {
        "title": "SQL Injection Prevention",
        "overview": "Provides guidelines to eliminate SQL Injection (SQLi) vulnerabilities by ensuring commands and parameters remain separated.",
        "bad_code": "```python\nquery = f\"SELECT * FROM users WHERE name = '{name}'\"\n```",
        "good_code": "```python\nquery = \"SELECT * FROM users WHERE name = :name\"\ndb.execute(query, {\"name\": name})\n```",
        "key_remediation": "1. Use parameterized queries/prepared statements exclusively.\n2. Utilize ORMs (SQLAlchemy, Hibernate) correctly.\n3. Validate inputs using strict type and pattern validation."
    },
    "cross_site_scripting_prevention": {
        "title": "Cross-Site Scripting Prevention",
        "overview": "Details actions to block malicious scripts from executing in client browsers.",
        "bad_code": "```html\n<div>{{ user_input | safe }}</div>\n```",
        "good_code": "```html\n<div>{{ user_input }}</div> <!-- Automatically escaped by template engine -->\n```",
        "key_remediation": "1. Perform context-aware output encoding (HTML, Javascript, CSS attributes).\n2. Enforce strict Content Security Policy (CSP).\n3. Set HttpOnly and Secure cookie parameters."
    },
    "cross_site_request_forgery_prevention": {
        "title": "Cross-Site Request Forgery Prevention",
        "overview": "Establishes defense mechanisms to prevent attackers from sending unauthorized commands from a user's browser.",
        "bad_code": "```python\n# VULNERABLE: API processes POST request without validating CSRF token\n```",
        "good_code": "```python\n# SECURE: Validate CSRF tokens on all state-changing requests (POST, PUT, DELETE)\n```",
        "key_remediation": "1. Implement double submit cookie patterns or synchronize tokens.\n2. Apply `SameSite=Strict` cookie policies.\n3. Protect sensitive endpoints behind re-authentication steps."
    },
    "password_storage": {
        "title": "Password Storage",
        "overview": "Specifies algorithms and workflows for storing user passwords securely.",
        "bad_code": "```python\nhash = hashlib.sha256(password.encode()).hexdigest()\n```",
        "good_code": "```python\n# SECURE: Argon2id with salt and memory controls\nph = PasswordHasher()\nhash = ph.hash(password)\n```",
        "key_remediation": "1. Never store passwords in plaintext or using symmetric encryption.\n2. Use Argon2id, bcrypt, or PBKDF2.\n3. Add unique salts and configure memory/work parameters high."
    },
    "session_management": {
        "title": "Session Management",
        "overview": "Best practices for managing user sessions and preventing token hijacking.",
        "bad_code": "```python\nresponse.set_cookie('sid', user_id)\n```",
        "good_code": "```python\nresponse.set_cookie('sid', session_id, httponly=True, secure=True, samesite='Strict')\n```",
        "key_remediation": "1. Use high-entropy session IDs.\n2. Regenerate IDs on login/privilege changes.\n3. Invalidate sessions on timeout or logout."
    },
    "jwt_security": {
        "title": "JWT Security",
        "overview": "Guidelines for safely generating, transmitting, and verifying JSON Web Tokens.",
        "bad_code": "```python\njwt.decode(token, options={\"verify_signature\": False})\n```",
        "good_code": "```python\njwt.decode(token, SECRET, algorithms=['HS256'])\n```",
        "key_remediation": "1. Enforce signature validation.\n2. Set short expiration (exp) and check signatures.\n3. Do not store sensitive details in JWT payload."
    },
    "input_validation": {
        "title": "Input Validation",
        "overview": "Establishes standard validation workflows for all application inputs.",
        "bad_code": "```python\n# VULNERABLE: Direct type parsing without format validation\nemail = req.args.get('email')\n```",
        "good_code": "```python\n# SECURE: Enforce email regex pattern check\nif not re.match(r'^\\S+@\\S+\\.\\S+$', email):\n    raise ValueError(\"Invalid email\")\n```",
        "key_remediation": "1. Validate type, range, length, and format.\n2. Use allowlists (regex for expected formats).\n3. Keep validation layers centralized."
    },
    "transport_layer_security": {
        "title": "Transport Layer Security",
        "overview": "Configurations for securing data in transit using TLS.",
        "bad_code": "```text\n# VULNERABLE: Supporting SSLv3, TLS 1.0, or weak RC4 ciphers\n```",
        "good_code": "```text\n# SECURE: Requiring TLS 1.2 or TLS 1.3 only, enforcing HSTS\n```",
        "key_remediation": "1. Disable HTTP access and redirect users to HTTPS.\n2. Set Strict-Transport-Security (HSTS).\n3. Use robust cipher suites (AES-GCM, CHACHA20)."
    },
    "file_upload": {
        "title": "File Upload",
        "overview": "Mitigates security risks when allowing users to upload documents to servers.",
        "bad_code": "```python\n# VULNERABLE: Saving file using user-provided filename on public server\nfile.save(os.path.join('/var/www/static', file.filename))\n```",
        "good_code": "```python\n# SECURE: Save file using secure UUID on isolated folder\nfilename = str(uuid.uuid4()) + \".txt\"\nfile.save(os.path.join('/tmp/uploads', filename))\n```",
        "key_remediation": "1. Rename uploaded files to UUIDs.\n2. Store uploads outside the web document root.\n3. Limit accepted mime-types and sizes."
    },
    "denial_of_service": {
        "title": "Denial of Service",
        "overview": "Defensive practices to mitigate Application Denial of Service (DoS) attacks.",
        "bad_code": "```python\n# VULNERABLE: Executing complex regex matching user input without limits\n```",
        "good_code": "```python\n# SECURE: Limit regex search duration and apply connection limits\n```",
        "key_remediation": "1. Apply rate-limiting controls.\n2. Limit request body sizes.\n3. Set timeouts on all read/write connection sockets."
    }
}

def create_directories():
    print("Creating directory structure...")
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Core directories
    dirs = [
        "security/owasp/cheat_sheets",
        "security/owasp/api_security",
        "security/owasp/asvs",
        "security/owasp/wstg",
        "security/owasp/proactive_controls",
        "metadata"
    ]
    
    # Generate Top 10 folders based on TOP10_DATA
    for cat_id, data in TOP10_DATA.items():
        folder_name = f"{cat_id}_" + data["title"].replace(' ', '_').replace('&', 'and')
        dirs.append(f"security/owasp/top10/{folder_name}")
        
    for d in dirs:
        path = os.path.join(BASE_DIR, d.replace('/', os.sep))
        os.makedirs(path, exist_ok=True)
    print("Directories created.")

def write_root_metadata():
    print("Writing root metadata files...")
    
    # README.md
    readme_content = """# CodeGuard V2 RAG Knowledge Base

Welcome to the CodeGuard V2 RAG Knowledge Base. This is a structured, comprehensive repository of application security and development standards, specifically optimized for Retrieval-Augmented Generation (RAG) pipelines.

## Structure
- `/security/owasp/`: OWASP Top 10, API Security, Proactive Controls, Cheat Sheets, ASVS, WSTG.
- `/metadata/`: Taxonomy and mapping datasets for system alignment.

## Usage
Each document in this knowledge base is modularly structured with a standard metadata frontmatter block, designed for precise semantic indexing and high-relevance chunk retrieval.
"""
    with open(os.path.join(BASE_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # KNOWLEDGE_INDEX.md
    index_content = """# Knowledge Base Index

This index lists the taxonomical paths and assets available in the knowledge base.

## Security (OWASP)
- **Top 10 (2021)**: `/security/owasp/top10/` (A01 - A10)
- **API Security**: `/security/owasp/api_security/` (API1 - API10)
- **Proactive Controls**: `/security/owasp/proactive_controls/` (C1 - C10)
- **Cheat Sheets**: `/security/owasp/cheat_sheets/` (Core prevention cheat sheets)

## Metadata Maps
- `/metadata/taxonomy.json`
- `/metadata/categories.json`
- `/metadata/source_registry.json`
"""
    with open(os.path.join(BASE_DIR, "KNOWLEDGE_INDEX.md"), "w", encoding="utf-8") as f:
        f.write(index_content)

    # DOCUMENT_SCHEMA.md
    schema_content = """# Document Schema

All knowledge documents in this repository must comply with the following schema:

```markdown
---
id: [TAXONOMY-ID]
title: [Document Title]
category: security
subcategory: owasp
language:
  - [languages (e.g. python, java)]
framework:
  - [frameworks (e.g. fastapi, spring_boot)]
severity: [critical|high|medium|low]
priority: [high|medium|low]
tags:
  - [tag1]
source: [Source Project]
source_url: [URL]
version: [version]
last_updated: [YYYY-MM-DD]
related:
  - [CWE-ID]
---

# Overview
# Why it matters
# Detection Rules
# Bad Code Patterns
# Good Code Patterns
# Common Mistakes
# Secure Alternatives
# Framework Notes
# Performance Considerations
# Related Standards
# References
```
"""
    with open(os.path.join(BASE_DIR, "DOCUMENT_SCHEMA.md"), "w", encoding="utf-8") as f:
        f.write(schema_content)

    # CATEGORY_MAPPING.md
    cat_content = """# Category Mapping

This document maps the relationships between OWASP Top 10, API Security, and CWEs.

| OWASP Category | Key CWEs | API Security Map | Proactive Controls |
|---|---|---|---|
| A01 Broken Access Control | CWE-200, CWE-284, CWE-285 | API1, API5 | C1, C6 |
| A02 Cryptographic Failures | CWE-311, CWE-327, CWE-328 | API2, API8 | C2, C9 |
| A03 Injection | CWE-89, CWE-78, CWE-79 | API7, API10 | C3, C4 |
| A04 Insecure Design | CWE-183, CWE-601 | API6 | C4, C5 |
| A05 Security Misconfiguration | CWE-2, CWE-16 | API8 | C5 |
| A06 Vulnerable Components | CWE-937, CWE-1035 | API9 | C6 |
| A07 Authentication Failures | CWE-287, CWE-307 | API2 | C7 |
| A08 Software Integrity Failures | CWE-502, CWE-494 | API10 | C6 |
| A09 Logging & Monitoring Failures | CWE-778, CWE-117 | API8 | C9 |
| A10 SSRF | CWE-918 | API7 | C10 |
"""
    with open(os.path.join(BASE_DIR, "CATEGORY_MAPPING.md"), "w", encoding="utf-8") as f:
        f.write(cat_content)

    # VERSION_HISTORY.md
    version_content = """# Version History

- **v2.0.0 (2026-07-19)**: Initial build of OWASP Security Knowledge Base for CodeGuard V2.
"""
    with open(os.path.join(BASE_DIR, "VERSION_HISTORY.md"), "w", encoding="utf-8") as f:
        f.write(version_content)

    # CONTRIBUTING.md
    contrib_content = """# Contributing Guidelines

1. Ensure all documents strictly follow the schema in `DOCUMENT_SCHEMA.md`.
2. Provide concrete, copy-pasteable Python and Java code snippets for vulnerable and secure patterns.
3. Map each vulnerability to its corresponding MITRE CWE identifier.
"""
    with open(os.path.join(BASE_DIR, "CONTRIBUTING.md"), "w", encoding="utf-8") as f:
        f.write(contrib_content)

    # SOURCES.md
    sources_content = """# Sources & References

- OWASP Top 10 Project: https://owasp.org/www-project-top-ten/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- OWASP API Security Project: https://owasp.org/www-project-api-security/
- OWASP Top 10 Proactive Controls: https://owasp.org/www-project-proactive-controls/
"""
    with open(os.path.join(BASE_DIR, "SOURCES.md"), "w", encoding="utf-8") as f:
        f.write(sources_content)

    # JSON Metadata files
    taxonomy = {
        "categories": {
            "security": {
                "owasp": ["top10", "api_security", "proactive_controls", "cheat_sheets"]
            }
        }
    }
    with open(os.path.join(BASE_DIR, "metadata", "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2)

    categories = {
        "A01": "Broken Access Control",
        "A02": "Cryptographic Failures",
        "A03": "Injection",
        "A04": "Insecure Design",
        "A05": "Security Misconfiguration",
        "A06": "Vulnerable Components",
        "A07": "Authentication Failures",
        "A08": "Software Data Integrity",
        "A09": "Logging Monitoring",
        "A10": "Server Side Request Forgery"
    }
    with open(os.path.join(BASE_DIR, "metadata", "categories.json"), "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)

    print("Root metadata files written.")

def generate_top10():
    print("Generating OWASP Top 10 documents...")
    
    frontmatter_template = """---
id: OWASP-{cat_id}
title: {title}
category: security
subcategory: owasp
language:
  - python
  - java
framework:
  - fastapi
  - spring_boot
severity: {severity}
priority: {priority}
tags:
  - {tag_list}
source: OWASP Top 10 2021
source_url: {source_url}
version: 2021
last_updated: 2026-07-19
related:
  - {cwe_list}
---
"""
    
    for cat_id, data in TOP10_DATA.items():
        folder_name = f"{cat_id}_" + data["title"].replace(' ', '_').replace('&', 'and')
        base_path = os.path.join(BASE_DIR, "security", "owasp", "top10", folder_name)
        
        tag_list = "\n  - ".join(data["tags"])
        cwe_list = "\n  - ".join(data["cwes"])
        
        # 1. overview.md
        overview_content = frontmatter_template.format(
            cat_id=cat_id, title=f"{data['title']} - Overview", severity=data["severity"],
            priority=data["priority"], tag_list=tag_list, source_url=data["source_url"], cwe_list=cwe_list
        ) + f"""
# Overview
{data['overview']}

# Why it matters
{data['why_it_matters']}

# Detection Rules
*Refer to [detection.md](detection.md) for details on detecting this vulnerability.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
{data['related_standards']}

# References
{data['references']}
"""

        # 2. detection.md
        detection_content = frontmatter_template.format(
            cat_id=cat_id, title=f"{data['title']} - Detection", severity=data["severity"],
            priority=data["priority"], tag_list=tag_list, source_url=data["source_url"], cwe_list=cwe_list
        ) + f"""
# Overview
*Refer to [overview.md](overview.md) for vulnerability details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
{data['detection_rules']}

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for code patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for code patterns.*

# Common Mistakes
{data['common_mistakes']}

# Secure Alternatives
*Refer to [remediation.md](remediation.md) for details.*

# Framework Notes
*Refer to [remediation.md](remediation.md) for details.*

# Performance Considerations
{data['performance_considerations']}

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
"""

        # 3. vulnerable_patterns.md
        vuln_content = frontmatter_template.format(
            cat_id=cat_id, title=f"{data['title']} - Vulnerable Patterns", severity=data["severity"],
            priority=data["priority"], tag_list=tag_list, source_url=data["source_url"], cwe_list=cwe_list
        ) + f"""
# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
{data['bad_code_patterns']}

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
"""

        # 4. secure_patterns.md
        secure_content = frontmatter_template.format(
            cat_id=cat_id, title=f"{data['title']} - Secure Patterns", severity=data["severity"],
            priority=data["priority"], tag_list=tag_list, source_url=data["source_url"], cwe_list=cwe_list
        ) + f"""
# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
{data['good_code_patterns']}

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
"""

        # 5. remediation.md
        remediation_content = frontmatter_template.format(
            cat_id=cat_id, title=f"{data['title']} - Remediation", severity=data["severity"],
            priority=data["priority"], tag_list=tag_list, source_url=data["source_url"], cwe_list=cwe_list
        ) + f"""
# Overview
*Refer to [overview.md](overview.md) for details.*

# Why it matters
*Refer to [overview.md](overview.md) for details.*

# Detection Rules
*Refer to [detection.md](detection.md) for details.*

# Bad Code Patterns
*Refer to [vulnerable_patterns.md](vulnerable_patterns.md) for vulnerable patterns.*

# Good Code Patterns
*Refer to [secure_patterns.md](secure_patterns.md) for secure patterns.*

# Common Mistakes
*Refer to [detection.md](detection.md) for details.*

# Secure Alternatives
{data['secure_alternatives']}

# Framework Notes
{data['framework_notes']}

# Performance Considerations
*Refer to [detection.md](detection.md) for details.*

# Related Standards
*Refer to [overview.md](overview.md) for standards.*

# References
*Refer to [overview.md](overview.md) for references.*
"""

        for name, content in [("overview.md", overview_content), ("detection.md", detection_content),
                              ("vulnerable_patterns.md", vuln_content), ("secure_patterns.md", secure_content),
                              ("remediation.md", remediation_content)]:
            with open(os.path.join(base_path, name), "w", encoding="utf-8") as f:
                f.write(content)
                
    print("OWASP Top 10 generated.")

def generate_api_security():
    print("Generating API Security documents...")
    
    frontmatter_template = """---
id: OWASP-{api_id}
title: {title}
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
  - api-security
  - {tag}
source: OWASP API Security Top 10 2023
source_url: https://owasp.org/www-project-api-security/
version: 2023
last_updated: 2026-07-19
related:
  - {related}
---
"""
    
    for api_id, data in API_DATA.items():
        filename = f"{api_id}_" + data["title"].replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and') + ".md"
        base_path = os.path.join(BASE_DIR, "security", "owasp", "api_security")
        
        content = frontmatter_template.format(
            api_id=api_id, title=data["title"], tag=data["title"].lower().replace(' ', '-'),
            related=data["related"]
        ) + f"""
# Overview
{data['overview']}

# Why it matters
{data['why_it_matters']}

# Detection Rules
{data['detection_rules']}

# Bad Code Patterns
{data['bad_code']}

# Good Code Patterns
{data['good_code']}

# Common Mistakes
{data['common_mistakes']}

# Secure Alternatives
{data['secure_alternatives']}

# Framework Notes
{data['framework_notes']}

# Performance Considerations
{data['performance']}

# Related Standards
{data['related']}

# References
{data['references']}
"""
        with open(os.path.join(base_path, filename), "w", encoding="utf-8") as f:
            f.write(content)
            
    print("API Security generated.")

def generate_proactive_controls():
    print("Generating Proactive Controls...")
    
    frontmatter_template = """---
id: OWASP-{ctrl_id}
title: {title}
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
  - {tag}
source: OWASP Top 10 Proactive Controls 2018
source_url: https://owasp.org/www-project-proactive-controls/
version: 2018
last_updated: 2026-07-19
related:
  - {related}
---
"""
    
    for ctrl_id, data in PROACTIVE_DATA.items():
        filename = f"{ctrl_id}_" + data["title"].replace(' ', '_').replace('&', 'and') + ".md"
        base_path = os.path.join(BASE_DIR, "security", "owasp", "proactive_controls")
        
        content = frontmatter_template.format(
            ctrl_id=ctrl_id, title=data["title"], tag=data["title"].lower().replace(' ', '-'),
            related=data["related"]
        ) + f"""
# Overview
{data['overview']}

# Why it matters
{data['why_it_matters']}

# Detection Rules
{data['detection_rules']}

# Bad Code Patterns
{data['bad_code']}

# Good Code Patterns
{data['good_code']}

# Common Mistakes
{data['common_mistakes']}

# Secure Alternatives
{data['secure_alternatives']}

# Framework Notes
{data['framework_notes']}

# Performance Considerations
{data['performance']}

# Related Standards
{data['related']}

# References
{data['references']}
"""
        with open(os.path.join(base_path, filename), "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Proactive Controls generated.")

def generate_cheat_sheets():
    print("Generating Cheat Sheets...")
    
    frontmatter_template = """---
id: OWASP-CS-{name_clean}
title: {title} Cheat Sheet
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
  - {name_clean}
source: OWASP Cheat Sheet Series
source_url: https://cheatsheetseries.owasp.org/
version: 2025
last_updated: 2026-07-19
related:
  - CWE-20
---
"""
    
    for name, data in CHEAT_DATA.items():
        filename = f"{name}.md"
        base_path = os.path.join(BASE_DIR, "security", "owasp", "cheat_sheets")
        
        content = frontmatter_template.format(
            name_clean=name.replace('_', '-'), title=data["title"]
        ) + f"""
# Overview
{data['overview']}

# Why it matters
This prevention guide covers standardized secure design constraints to completely mitigate issues related to {data['title']}.

# Detection Rules
Configure validation checkers and linters to enforce pattern checks defined in this guide.

# Bad Code Patterns
{data['bad_code']}

# Good Code Patterns
{data['good_code']}

# Common Mistakes
- Misconfiguring libraries or using insecure API options.
- Lacking unit tests to verify security controls.

# Secure Alternatives
{data['key_remediation']}

# Framework Notes
Choose secure modern frameworks that build these protections in by default.

# Performance Considerations
Proper implementation (e.g. prepared statements) often speeds up execution by enabling optimization caches.

# Related Standards
Refer to ASVS and WSTG guides.

# References
OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/cheatsheets/{name}.html
"""
        with open(os.path.join(base_path, filename), "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Cheat Sheets generated.")

if __name__ == "__main__":
    create_directories()
    write_root_metadata()
    generate_top10()
    generate_api_security()
    generate_proactive_controls()
    generate_cheat_sheets()
    print("All tasks completed successfully!")
