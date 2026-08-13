import os
import json
import yaml

BASE_DIR = r"d:\RAG\knowledge\security\owasp"
ASVS_DIR = os.path.join(BASE_DIR, "asvs")
WSTG_DIR = os.path.join(BASE_DIR, "wstg")

os.makedirs(ASVS_DIR, exist_ok=True)
os.makedirs(WSTG_DIR, exist_ok=True)

print("Starting ASVS and WSTG Complete Knowledge Base Builder...")

# Helper to populate defaults if missing
def sanitize_item(item, default_type="asvs"):
    required_keys = [
        "title", "severity", "priority", "cwe", "top10", "cheat_sheet",
        "overview", "objective", "why", "threat_model", "ast_hints",
        "regex_hints", "semantic_hints", "apis", "imports", "bad_code",
        "good_code", "fastapi", "flask", "django", "sqlalchemy",
        "postgresql", "mistakes", "fps", "fns", "heuristics", "confidence",
        "reasoning", "remediation"
    ]
    if default_type == "asvs":
        required_keys.append("wstg")
        required_keys.append("req_id")
        required_keys.append("chapter")
    else:
        required_keys.append("asvs")
        required_keys.append("test_id")
        required_keys.append("category")
        
    for k in required_keys:
        if k not in item:
            item[k] = f"Standard security control for {item.get('title', 'rule')}."
    return item

ASVS_DATASET = [
    # V1 Architecture
    {
        "subfolder": "v1_architecture",
        "req_id": "V1.1.1",
        "title": "Secure Architecture & Subsystem Isolation",
        "chapter": "V1 Architecture",
        "severity": "high", "priority": "high", "cwe": "CWE-657", "top10": "A04:2021-Insecure Design",
        "cheat_sheet": "Architecture_Concepts_Cheat_Sheet", "wstg": "WSTG-INFO-10",
        "overview": "Verify that all application components and subsystems are isolated with explicit trust boundaries and least-privilege security controls.",
        "objective": "Prevent horizontal and vertical privilege escalation by ensuring strict separation of concerns and network segmentation between microservices.",
        "why": "Unsegmented monolithic systems allow an attacker who compromises a low-privilege component to pivot to sensitive database credentials or admin logic.",
        "threat_model": "Attacker leverages remote code execution in a perimeter subsystem to read environment variables and connect to unauthenticated internal microservices.",
        "ast_hints": "ast.Import, ast.ImportFrom (os, sys, subprocess, socket), ast.Call (exec, eval, system)",
        "regex_hints": r"(?i)(exec|eval|os\.system|subprocess\.Popen|socket\.connect|0\.0\.0\.0)",
        "semantic_hints": "Direct invocation of system modules across untrusted API routes without isolation barriers.",
        "apis": "os.system, subprocess.run, socket.socket, shutil.rmtree", "imports": "import os, import subprocess, import socket, import sys",
        "bad_code": "def process_task(cmd):\n    # VULNERABLE\n    os.system(f'run_job {cmd}')",
        "good_code": "def process_task(cmd_name: str):\n    # SECURE: Allowlist validation\n    ALLOWED = {'sync': '/bin/sync_job'}\n    if cmd_name not in ALLOWED: raise ValueError('Denied')\n    subprocess.run([ALLOWED[cmd_name]], check=True)",
        "fastapi": "@app.post('/task')\ndef run_task(user=Depends(require_admin)):\n    return {'status': 'queued'}",
        "flask": "@app.route('/task', methods=['POST'])\ndef run_task():\n    if not g.user.is_admin: abort(403)\n    return {'status': 'queued'}",
        "django": "def run_task(request):\n    if not request.user.is_superuser: return HttpResponseForbidden()\n    return JsonResponse({'status': 'queued'})",
        "sqlalchemy": "engine = create_engine(DATABASE_READONLY_URL)",
        "postgresql": "GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;",
        "mistakes": "Mixing administrative and public API routes in the same unsegmented process without role middleware.",
        "fps": "Internal administrative scripts executed strictly within dedicated CLI management commands.",
        "fns": "Implicit trust granted to internal microservices without validating JWT bearer tokens.",
        "heuristics": "Flag any endpoint invoking OS processes or raw sockets without explicit role dependency checks.",
        "confidence": "high", "reasoning": "Trace user input parameters to sink functions. Verify authorization guards prior to sink invocation.",
        "remediation": "Implement strict authorization middleware and segment database permissions by subsystem role."
    },
    # V2 Authentication
    {
        "subfolder": "v2_authentication",
        "req_id": "V2.1.1",
        "title": "Password Length & Complexity Verification",
        "chapter": "V2 Authentication",
        "severity": "high", "priority": "high", "cwe": "CWE-521", "top10": "A07:2021-Identification and Authentication Failures",
        "cheat_sheet": "Authentication_Cheat_Sheet", "wstg": "WSTG-ATHN-07",
        "overview": "Verify that user passwords are required to be at least 12 characters in length and checked against compromised credential lists.",
        "objective": "Enforce strong user password policies that withstand brute-force attacks and dictionary matching.",
        "why": "Short passwords are susceptible to offline brute-force attacks and dictionary matching.",
        "threat_model": "Attacker uses automated credential stuffing to compromise accounts using common short passwords.",
        "ast_hints": "ast.Compare, ast.Call (len, check_password, validate_password)",
        "regex_hints": r"(?i)len\(\s*password\s*\)\s*<\s*(8|10|12)",
        "semantic_hints": "Weak password length validations allowing passwords under 12 characters.",
        "apis": "len(), passlib.hash.argon2, werkzeug.security.check_password_hash", "imports": "from passlib.hash import argon2, import re",
        "bad_code": "def validate_password(p):\n    if len(p) < 6: raise ValueError('Short')",
        "good_code": "def validate_password(p):\n    if len(p) < 12: raise ValueError('Must be 12+ chars')",
        "fastapi": "class UserReg(BaseModel):\n    password: str = Field(..., min_length=12)",
        "flask": "if len(request.json.get('password', '')) < 12: return jsonify({'error': 'Too short'}), 400",
        "django": "AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}}]",
        "sqlalchemy": "# Validate password length before setting password hash on User model",
        "postgresql": "-- Enforce password length at app registration layer",
        "mistakes": "Restricting password character sets or enforcing arbitrary truncation.",
        "fps": "Custom password strength estimators like zxcvbn enforcing entropy instead of strict character counts.",
        "fns": "Checking password length on hashed strings instead of raw password inputs.",
        "heuristics": "Flag any password field validation enforcing min_length less than 12.",
        "confidence": "high", "reasoning": "Locate password validation logic and check min_length >= 12.",
        "remediation": "Update password validation schema to enforce minimum length of 12 characters."
    },
    # V3 Session Management
    {
        "subfolder": "v3_session_management",
        "req_id": "V3.2.1",
        "title": "Session Binding & Cookie Security Flags",
        "chapter": "V3 Session Management",
        "severity": "high", "priority": "high", "cwe": "CWE-614", "top10": "A05:2021-Security Misconfiguration",
        "cheat_sheet": "Session_Management_Cheat_Sheet", "wstg": "WSTG-SESS-02",
        "overview": "Verify that session cookies have HttpOnly, Secure, and SameSite flags set to prevent XSS theft and CSRF.",
        "objective": "Ensure session identifiers are cryptographically bound and protected from client-side script theft and cross-site requests.",
        "why": "Missing HttpOnly allows attackers executing XSS to read document.cookie and hijack sessions.",
        "threat_model": "Attacker intercepts unencrypted session cookie over public Wi-Fi or steals session token via XSS.",
        "ast_hints": "ast.Call (set_cookie, set_cookie_header)",
        "regex_hints": r"(?i)set_cookie\((?:(?!httponly=True).)*\)",
        "semantic_hints": "Cookie issuance without HttpOnly=True, Secure=True, and SameSite=Lax/Strict.",
        "apis": "Response.set_cookie, set_cookie", "imports": "from fastapi import Response, from flask import make_response",
        "bad_code": "response.set_cookie('session_id', token)",
        "good_code": "response.set_cookie('session_id', token, httponly=True, secure=True, samesite='Strict')",
        "fastapi": "response.set_cookie(key='session_id', value=token, httponly=True, secure=True, samesite='lax')",
        "flask": "resp = make_response(render_template('index.html'))\nresp.set_cookie('session_id', token, httponly=True, secure=True, samesite='Lax')",
        "django": "SESSION_COOKIE_HTTPONLY = True\nSESSION_COOKIE_SECURE = True\nSESSION_COOKIE_SAMESITE = 'Lax'",
        "sqlalchemy": "# Store hashed session tokens in database session table",
        "postgresql": "-- Store hashed session tokens in DB table",
        "mistakes": "Setting `samesite='None'` without enforcing `secure=True`.",
        "fps": "Setting cookies for non-sensitive public preferences without HttpOnly.",
        "fns": "Setting correct flags on custom cookies but omitting them on framework session defaults.",
        "heuristics": "Flag all `set_cookie` calls where `httponly` or `secure` is False or absent.",
        "confidence": "high", "reasoning": "Scan set_cookie invocations and check for missing HttpOnly, Secure, SameSite parameters.",
        "remediation": "Add `httponly=True`, `secure=True`, and `samesite='Lax'` to all session cookie assignments."
    },
    # V4 Access Control
    {
        "subfolder": "v4_access_control",
        "req_id": "V4.1.1",
        "title": "Access Control Enforcement (Deny by Default)",
        "chapter": "V4 Access Control",
        "severity": "critical", "priority": "high", "cwe": "CWE-285", "top10": "A01:2021-Broken Access Control",
        "cheat_sheet": "Authorization_Cheat_Sheet", "wstg": "WSTG-ATHZ-02",
        "overview": "Verify that access control is enforced on every request and denies access by default.",
        "objective": "Deny all unauthorized request access attempts unless explicitly permitted by authorization rules.",
        "why": "Failure to enforce access control permits unauthenticated or low-privileged users to invoke restricted functionality.",
        "threat_model": "Attacker accesses `/api/admin/users` directly because route lacks authorization decorator.",
        "ast_hints": "ast.FunctionDef, ast.ClassDef, ast.Decorator",
        "regex_hints": r"(?i)@(app|router)\.(get|post|put|delete)\([^)]*\)(?!\s*@(?:login_required|permission))",
        "semantic_hints": "Exposing endpoint routes without explicit authentication or authorization middleware dependencies.",
        "apis": "Depends(get_current_user), login_required, permission_required", "imports": "from fastapi import Depends, from flask_login import login_required",
        "bad_code": "@app.get('/admin/data')\ndef get_admin_data(): return db.query_all()",
        "good_code": "@app.get('/admin/data')\ndef get_admin_data(user=Depends(require_admin_user)): return db.query_all()",
        "fastapi": "def require_admin(user=Depends(get_current_user)):\n    if not user.is_admin: raise HTTPException(403)\n    return user",
        "flask": "@app.route('/admin/data')\n@login_required\ndef get_admin_data():\n    if not current_user.is_admin: abort(403)\n    return jsonify(db.get_admin_data())",
        "django": "@user_passes_test(lambda u: u.is_superuser)\ndef admin_view(request): return render(request, 'admin.html')",
        "sqlalchemy": "session.query(Record).filter(Record.tenant_id == current_user.tenant_id)",
        "postgresql": "ALTER TABLE records ENABLE ROW LEVEL SECURITY;",
        "mistakes": "Checking permissions in the frontend UI while leaving backend API endpoints exposed.",
        "fps": "Explicitly public endpoints such as `/health`, `/login`, or `/docs`.",
        "fns": "Checking authentication but omitting role/permission authorization checks on sensitive actions.",
        "heuristics": "Flag any state-changing API route lacking authorization dependencies.",
        "confidence": "high", "reasoning": "Verify presence of authentication and authorization decorators on route definitions.",
        "remediation": "Apply centralized authorization middleware or require user context dependency on all routes."
    },
    # V5 Validation & Sanitization
    {
        "subfolder": "v5_validation_sanitization",
        "req_id": "V5.3.1",
        "title": "Parameterized SQL Database Queries",
        "chapter": "V5 Validation, Sanitization & Encoding",
        "severity": "critical", "priority": "high", "cwe": "CWE-89", "top10": "A03:2021-Injection",
        "cheat_sheet": "SQL_Injection_Prevention_Cheat_Sheet", "wstg": "WSTG-INPV-05",
        "overview": "Verify that all database queries use parameterized SQL prepared statements to prevent SQL Injection.",
        "objective": "Ensure database queries separate SQL command structure from user parameters.",
        "why": "Dynamic string concatenation allows attackers to manipulate query logic and exfiltrate databases.",
        "threat_model": "Attacker inputs `' OR '1'='1` into login form to bypass authentication and dump entire table.",
        "ast_hints": "ast.Call (execute, raw, query), ast.JoinedStr (f-strings)",
        "regex_hints": r"(?i)(execute|raw)\(\s*f['\"].*SELECT|INSERT|UPDATE|DELETE",
        "semantic_hints": "Constructing SQL strings using format strings or `%` operators before passing to database execution sinks.",
        "apis": "cursor.execute, session.execute, text()", "imports": "from sqlalchemy import text, import psycopg2",
        "bad_code": "cursor.execute(f'SELECT * FROM users WHERE email = \"{user_input}\"')",
        "good_code": "cursor.execute('SELECT * FROM users WHERE email = %s', (user_input,))",
        "fastapi": "@app.get('/users')\ndef get_user(email: str, db: Session = Depends(get_db)):\n    return db.execute(text('SELECT * FROM users WHERE email = :e'), {'e': email}).fetchall()",
        "flask": "@app.route('/user')\ndef user():\n    e = request.args.get('email')\n    return jsonify(db.session.execute(text('SELECT * FROM users WHERE email = :e'), {'e': e}).fetchall())",
        "django": "User.objects.filter(email=user_input)",
        "sqlalchemy": "session.query(User).filter(User.email == user_input)",
        "postgresql": "PREPARE get_user (text) AS SELECT * FROM users WHERE email = $1;\nEXECUTE get_user('admin@example.com');",
        "mistakes": "Using ORMs but calling raw SQL helper methods with f-strings.",
        "fps": "Concatenating hardcoded static strings derived strictly from internal enum allowlists.",
        "fns": "Passing pre-formatted strings into ORM `.extra()` or `raw()` queries.",
        "heuristics": "Flag any `execute()` call where the query string is constructed via f-string or `%` formatting.",
        "confidence": "high", "reasoning": "Inspect database execution sinks and flag dynamic SQL string construction.",
        "remediation": "Replace all raw string formatted SQL statements with parameterized prepared statements."
    },
    # V6 Stored Cryptography
    {
        "subfolder": "v6_stored_cryptography",
        "req_id": "V6.2.1",
        "title": "Strong Cryptographic Algorithm Selection",
        "chapter": "V6 Stored Cryptography",
        "severity": "critical", "priority": "high", "cwe": "CWE-327", "top10": "A02:2021-Cryptographic Failures",
        "cheat_sheet": "Cryptographic_Storage_Cheat_Sheet", "wstg": "WSTG-CRYP-04",
        "overview": "Verify that strong cryptographic algorithms (such as AES-256-GCM or Argon2id) are used for encryption and hashing.",
        "objective": "Ensure stored sensitive data and passwords use industry-standard algorithms resilient to cryptanalysis.",
        "why": "Legacy ciphers (DES, RC4) and weak hash functions (MD5, SHA1) are vulnerable to rapid decryption and collision attacks.",
        "threat_model": "Attacker steals hashed password database and cracks MD5 hashes in minutes using GPU rainbow tables.",
        "ast_hints": "ast.Call (hashlib.md5, hashlib.sha1, DES.new)",
        "regex_hints": r"(?i)(md5|sha1|DES|RC4)\(",
        "semantic_hints": "Use of deprecated cipher suites or non-salted hash functions for password storage.",
        "apis": "hashlib.pbkdf2_hmac, cryptography.hazmat.primitives.ciphers.aead.AESGCM, argon2.PasswordHasher",
        "imports": "from cryptography.hazmat.primitives.ciphers.aead import AESGCM, from argon2 import PasswordHasher",
        "bad_code": "import hashlib\ndef hash_pass(p): return hashlib.md5(p.encode()).hexdigest()",
        "good_code": "from argon2 import PasswordHasher\nph = PasswordHasher()\ndef hash_pass(p): return ph.hash(p)",
        "fastapi": "pwd_context = CryptContext(schemes=['argon2', 'bcrypt'], deprecated='auto')",
        "flask": "hash_str = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)",
        "django": "PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher']",
        "sqlalchemy": "# Store Argon2 password hashes in VARCHAR(255) column",
        "postgresql": "CREATE EXTENSION pgcrypto;\nSELECT pgcrypto.crypt('password', pgcrypto.gen_salt('bf', 12));",
        "mistakes": "Implementing custom encryption logic or reusing static initialization vectors (IV).",
        "fps": "Using MD5 or SHA1 strictly for non-security checksums (e.g. file cache keys).",
        "fns": "Using strong ciphers but hardcoding the secret encryption key in source code.",
        "heuristics": "Flag any usage of MD5, SHA1, DES, or ECB mode in password or encryption workflows.",
        "confidence": "high", "reasoning": "Inspect algorithm parameters in hashing/encryption calls and flag obsolete ciphers.",
        "remediation": "Migrate password hashing to Argon2id/bcrypt and symmetric encryption to AES-256-GCM."
    },
    # V7 Error Handling & Logging
    {
        "subfolder": "v7_error_handling_logging",
        "req_id": "V7.1.1",
        "title": "Log Content Security & PII Protection",
        "chapter": "V7 Error Handling & Logging",
        "severity": "medium", "priority": "medium", "cwe": "CWE-532", "top10": "A09:2021-Security Logging and Monitoring Failures",
        "cheat_sheet": "Logging_Cheat_Sheet", "wstg": "WSTG-ERRH-01",
        "overview": "Verify that sensitive data such as passwords, tokens, PII, and credit card numbers are never logged in cleartext.",
        "objective": "Prevent sensitive user credentials and tokens from leaking into log storage or monitoring tools.",
        "why": "Logs accessible to operations staff can leak plain passwords and session keys if not redacted.",
        "threat_model": "Attacker compromises SIEM platform and reads plain text user passwords emitted during login exceptions.",
        "ast_hints": "ast.Call (logging.info, logger.debug, print)",
        "regex_hints": r"(?i)log(ger)?\.(info|debug|error)\(.*(password|secret|token|ssn|credit_card)",
        "semantic_hints": "Logging raw request headers or request bodies containing authentication credentials.",
        "apis": "logging.getLogger, structlog.get_logger", "imports": "import logging, import structlog",
        "bad_code": "logger.info(f'User login attempt: {username} with password: {password}')",
        "good_code": "logger.info('User login attempt', extra={'username': username, 'status': 'initiated'})",
        "fastapi": "@app.post('/login')\ndef login(credentials: LoginSchema):\n    logger.info('Login attempt for user=%s', credentials.username)",
        "flask": "@app.route('/login', methods=['POST'])\ndef login():\n    logger.info('Login endpoint called by ip=%s', request.remote_addr)",
        "django": "@sensitive_post_parameters('password')\ndef login_view(request): pass",
        "sqlalchemy": "engine = create_engine(DB_URL, echo=False)",
        "postgresql": "-- Set log_min_messages = warning to prevent logging bind parameters",
        "mistakes": "Printing raw exception objects `logger.error(ex)` containing full request strings with passwords.",
        "fps": "Logging masked or hashed identifier tokens.",
        "fns": "Filtering form parameters but failing to redact sensitive JSON body attributes.",
        "heuristics": "Flag any log call formatting variables named `password`, `secret`, or `token`.",
        "confidence": "high", "reasoning": "Inspect log statement format strings and flag sensitive credential logging.",
        "remediation": "Redact or mask sensitive credentials from log payloads prior to output stream."
    },
    # V8 Data Protection
    {
        "subfolder": "v8_data_protection",
        "req_id": "V8.1.1",
        "title": "Sensitive Data In-Memory & Storage Protection",
        "chapter": "V8 Data Protection",
        "severity": "high", "priority": "high", "cwe": "CWE-311", "top10": "A02:2021-Cryptographic Failures",
        "cheat_sheet": "Cryptographic_Storage_Cheat_Sheet", "wstg": "WSTG-CRYP-03",
        "overview": "Verify that sensitive data at rest is protected with strong encryption and appropriate access controls.",
        "objective": "Ensure all persistent database fields containing PII, financial details, or secrets are encrypted at rest.",
        "why": "Unencrypted database backups or compromised storage volumes expose sensitive records to unauthorized disclosure.",
        "threat_model": "Attacker steals unencrypted database backup file from S3 bucket and extracts user social security numbers.",
        "ast_hints": "ast.ClassDef (SQLAlchemy models), ast.Call (Fernet, AESGCM)",
        "regex_hints": r"(?i)(ssn|credit_card|secret_key)\s*=\s*Column\(String",
        "semantic_hints": "Storing PII fields in plain text database columns without encryption layers.",
        "apis": "cryptography.fernet.Fernet, sqlalchemy_utils.EncryptedType", "imports": "from cryptography.fernet import Fernet, from sqlalchemy_utils import EncryptedType",
        "bad_code": "class User(Base):\n    ssn = Column(String) # VULNERABLE",
        "good_code": "class User(Base):\n    ssn = Column(EncryptedType(String, secret_key, FernetEngine)) # SECURE",
        "fastapi": "user.ssn = fernet.encrypt(raw_ssn.encode()).decode()",
        "flask": "raw_ssn = fernet.decrypt(user.encrypted_ssn.encode()).decode()",
        "django": "class Profile(models.Model):\n    ssn = EncryptedCharField(max_length=100)",
        "sqlalchemy": "ssn = Column(EncryptedType(String, secret_key, FernetEngine))",
        "postgresql": "INSERT INTO users (ssn) VALUES (pgp_sym_encrypt('123-45-6789', 'AES_KEY'));",
        "mistakes": "Encrypting data with keys stored directly alongside the database in the same container.",
        "fps": "Hashing non-reversible tokens (like password hashes) which do not require encryption at rest.",
        "fns": "Encrypting primary database tables but failing to encrypt database dump files or redis caches.",
        "heuristics": "Flag database model fields holding sensitive labels defined as raw String without encryption wrapper.",
        "confidence": "high", "reasoning": "Inspect database model definitions and check for missing cipher wrappers on PII fields.",
        "remediation": "Apply column-level encryption or transparent data encryption (TDE) for sensitive database fields."
    },
    # V9 Communications
    {
        "subfolder": "v9_communications",
        "req_id": "V9.1.1",
        "title": "TLS Protocol Configuration and Cipher Suite Security",
        "chapter": "V9 Communications",
        "severity": "high", "priority": "high", "cwe": "CWE-326", "top10": "A02:2021-Cryptographic Failures",
        "cheat_sheet": "Transport_Layer_Security_Cheat_Sheet", "wstg": "WSTG-CRYP-01",
        "overview": "Verify that all network communications use TLS 1.2 or TLS 1.3 with strong cipher suites.",
        "objective": "Ensure all client-server and server-server network channels enforce secure TLS protocols.",
        "why": "Supporting obsolete SSLv3 or TLS 1.0 protocols leaves communication channels vulnerable to downgrade attacks.",
        "threat_model": "Attacker conducts man-in-the-middle attack to force client connection downgrade to TLS 1.0.",
        "ast_hints": "ast.Call (ssl.create_default_context, ssl.SSLContext)",
        "regex_hints": r"(?i)(PROTOCOL_SSLv23|PROTOCOL_TLSv1|PROTOCOL_TLSv1_1)",
        "semantic_hints": "Configuring SSL contexts to allow deprecated TLS protocols or insecure cipher choices.",
        "apis": "ssl.create_default_context, ssl.PROTOCOL_TLS_CLIENT", "imports": "import ssl",
        "bad_code": "context = ssl.SSLContext(ssl.PROTOCOL_TLSv1) # VULNERABLE",
        "good_code": "context = ssl.create_default_context()\ncontext.minimum_version = ssl.TLSVersion.TLSv1_2 # SECURE",
        "fastapi": "# Gunicorn --ssl-version TLSv1_2 --ssl-ciphers ECDHE-ECDSA-AES256-GCM-SHA384",
        "flask": "app.run(ssl_context=context)",
        "django": "# Enforced at reverse proxy level (Nginx/Traefik)",
        "sqlalchemy": "engine = create_engine('postgresql://user:pass@db:5432/app?sslmode=verify-full')",
        "postgresql": "ssl_min_protocol_version = 'TLSv1.2'",
        "mistakes": "Disabling SSL certificate verification (`verify=False` in requests module).",
        "fps": "Internal loopback socket communication between processes on the same isolated host.",
        "fns": "Enforcing TLS 1.2 on web traffic while leaving backend database connections unencrypted.",
        "heuristics": "Flag any SSLContext setup allowing TLS versions below 1.2 or setting `check_hostname = False`.",
        "confidence": "high", "reasoning": "Verify minimum protocol version settings in SSLContext instantiations.",
        "remediation": "Set `minimum_version = ssl.TLSVersion.TLSv1_2` and restrict cipher suites to modern GCM algorithms."
    },
    # V10 Malicious Code
    {
        "subfolder": "v10_malicious_code",
        "req_id": "V10.1.1",
        "title": "Safe Serialization & Deserialization Prevention",
        "chapter": "V10 Malicious Code",
        "severity": "critical", "priority": "high", "cwe": "CWE-502", "top10": "A08:2021-Software and Data Integrity Failures",
        "cheat_sheet": "Deserialization_Cheat_Sheet", "wstg": "WSTG-INPV-11",
        "overview": "Verify that untrusted data is never deserialized using insecure object serializers like pickle, marshal, or PyYAML unsafe loads.",
        "objective": "Prevent Remote Code Execution (RCE) by avoiding execution of arbitrary code during object reconstruction.",
        "why": "Insecure deserialization of arbitrary payloads allows attackers to instantiate dangerous objects and execute arbitrary shell commands.",
        "threat_model": "Attacker crafts malicious `__reduce__` pickle payload sent in cookie to achieve full server shell execution.",
        "ast_hints": "ast.Call (pickle.loads, marshal.loads, yaml.load)",
        "regex_hints": r"(?i)(pickle\.loads|marshal\.loads|yaml\.load\([^,)]*\))",
        "semantic_hints": "Deserializing binary stream or user-supplied string data into Python objects using unsafe methods.",
        "apis": "json.loads, pydantic.BaseModel.parse_raw, yaml.safe_load", "imports": "import json, import pydantic, import yaml",
        "bad_code": "import pickle\n@app.post('/session')\ndef restore(data: bytes): return pickle.loads(data)",
        "good_code": "import json\n@app.post('/session')\ndef restore(data: str): return json.loads(data)",
        "fastapi": "class SessionSchema(BaseModel):\n    user_id: int\n@app.post('/session')\ndef restore(p: SessionSchema): return p",
        "flask": "data = request.get_json()",
        "django": "SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'",
        "sqlalchemy": "# Avoid MutableDict with pickle storage in SQLAlchemy column definitions",
        "postgresql": "-- Store semi-structured data using native jsonb data type",
        "mistakes": "Using `yaml.load(data)` without specifying `Loader=yaml.SafeLoader`.",
        "fps": "Deserializing trusted internal static configuration files packaged strictly within deployment artifact.",
        "fns": "Replacing `pickle` with `shelve` or `dill` which remain vulnerable to insecure object instantiation.",
        "heuristics": "Flag all occurrences of `pickle.loads()`, `marshal.loads()`, or `yaml.load()` without SafeLoader.",
        "confidence": "high", "reasoning": "Locate object deserialization method calls and flag use of pickle or unsafe PyYAML.",
        "remediation": "Replace pickle and unsafe serializers with JSON, Protocol Buffers, or Pydantic schemas."
    },
    # V11 Business Logic
    {
        "subfolder": "v11_business_logic",
        "req_id": "V11.1.1",
        "title": "Business Logic Integrity & Workflow Enforcement",
        "chapter": "V11 Business Logic",
        "severity": "high", "priority": "high", "cwe": "CWE-840", "top10": "A04:2021-Insecure Design",
        "cheat_sheet": "Business_Logic_Security_Cheat_Sheet", "wstg": "WSTG-BUSL-04",
        "overview": "Verify that application business workflows enforce step ordering and state validation to prevent workflow circumvention.",
        "objective": "Ensure multi-step business flows cannot be skipped or manipulated to bypass validation steps.",
        "why": "Attackers can bypass step 2 (payment confirmation) and jump directly to step 3 (order delivery) if state is not verified server-side.",
        "threat_model": "Attacker submits HTTP request directly to `/checkout/success` with arbitrary order ID without paying.",
        "ast_hints": "ast.FunctionDef, ast.If (state checks)",
        "regex_hints": r"(?i)def (checkout_complete|order_fulfill)",
        "semantic_hints": "Executing high-privilege business actions without checking current transaction state in backend database.",
        "apis": "db.session.query, state_machine.validate", "imports": "from enum import Enum",
        "bad_code": "@app.post('/order/complete')\ndef complete(order_id: int): db.mark_fulfilled(order_id)",
        "good_code": "@app.post('/order/complete')\ndef complete(order_id: int):\n    order = db.get_order(order_id)\n    if order.status != OrderStatus.PAID: raise HTTPException(400, 'Not paid')\n    order.status = OrderStatus.FULFILLED; db.commit()",
        "fastapi": "@app.post('/checkout/fulfill')\ndef fulfill(order_id: int, db: Session = Depends(get_db)):\n    order = db.query(Order).filter(Order.id == order_id).first()\n    if not order or order.status != 'PAID': raise HTTPException(400)\n    order.status = 'FULFILLED'; db.commit()",
        "flask": "@app.route('/checkout/fulfill', methods=['POST'])\ndef fulfill():\n    order = Order.query.get_or_404(request.json['order_id'])\n    if order.status != 'PAID': abort(400)\n    order.status = 'FULFILLED'; db.session.commit()",
        "django": "def fulfill(request, order_id):\n    order = get_object_or_404(Order, id=order_id)\n    if order.status != OrderStatus.PAID: return HttpResponseBadRequest()\n    order.status = OrderStatus.FULFILLED; order.save()",
        "sqlalchemy": "# Enforce state machine transition checks in SQLAlchemy ORM event listeners",
        "postgresql": "ALTER TABLE orders ADD CONSTRAINT check_status CHECK (status IN ('PENDING', 'PAID', 'FULFILLED'));",
        "mistakes": "Relying on client session variables to track multi-step form progress instead of database state.",
        "fps": "Idempotent administrative status override endpoints reserved for customer support roles.",
        "fns": "Checking state flags but failing to lock the database row, opening window for race conditions.",
        "heuristics": "Flag state-updating methods that omit explicit status verification prior to mutation.",
        "confidence": "high", "reasoning": "Locate state-changing business handlers and verify prerequisite state checks.",
        "remediation": "Implement server-side state machines and validate state preconditions before processing workflow steps."
    },
    # V12 File & Resources
    {
        "subfolder": "v12_files_resources",
        "req_id": "V12.1.1",
        "title": "Secure File Upload & Path Sanitization",
        "chapter": "V12 File & Resources",
        "severity": "critical", "priority": "high", "cwe": "CWE-434", "top10": "A04:2021-Insecure Design",
        "cheat_sheet": "File_Upload_Cheat_Sheet", "wstg": "WSTG-BUSL-07",
        "overview": "Verify that uploaded files are validated for type, renamed with generated UUIDs, and stored outside the web root.",
        "objective": "Prevent arbitrary code execution and path traversal via malicious file uploads.",
        "why": "Uploading executable scripts (e.g. `.py`, `.php`) to web-accessible directories allows remote attackers to execute code on server.",
        "threat_model": "Attacker uploads `shell.py` or filename `../../etc/passwd` to overwrite critical system files.",
        "ast_hints": "ast.Call (save, open, write, UploadFile)",
        "regex_hints": r"(?i)\.save\(\s*file\.filename\)",
        "semantic_hints": "Saving user-uploaded files directly using original filename without sanitization or UUID re-naming.",
        "apis": "werkzeug.utils.secure_filename, uuid.uuid4, path.join", "imports": "import uuid, os, from werkzeug.utils import secure_filename",
        "bad_code": "@app.post('/upload')\ndef upload(file: UploadFile):\n    with open(f'/var/www/uploads/{file.filename}', 'wb') as f: f.write(file.file.read())",
        "good_code": "@app.post('/upload')\ndef upload(file: UploadFile):\n    ext = os.path.splitext(file.filename)[1].lower()\n    if ext not in ('.jpg', '.png'): raise HTTPException(400)\n    name = f'{uuid.uuid4()}{ext}'\n    with open(os.path.join('/var/app_storage', name), 'wb') as f: f.write(file.file.read())",
        "fastapi": "@app.post('/upload')\ndef upload_file(file: UploadFile = File(...)):\n    ext = os.path.splitext(file.filename)[1].lower()\n    if ext not in ('.png', '.jpg'): raise HTTPException(400)\n    filename = f'{uuid.uuid4()}{ext}'\n    dest = os.path.join('/tmp/uploads', filename)\n    with open(dest, 'wb') as buffer: shutil.copyfileobj(file.file, buffer)",
        "flask": "@app.route('/upload', methods=['POST'])\ndef upload():\n    f = request.files['file']\n    safe_name = f'{uuid.uuid4()}_{secure_filename(f.filename)}'\n    f.save(os.path.join('/var/uploads', safe_name))",
        "django": "def handle_upload(request):\n    f = request.FILES['file']\n    filename = f'{uuid.uuid4()}_{f.name}'\n    default_storage.save(f'uploads/{filename}', f)",
        "sqlalchemy": "# Store file metadata and generated storage path in database",
        "postgresql": "-- Store file record details (uuid, mime_type, byte_size, storage_path)",
        "mistakes": "Validating Content-Type header only, which can be spoofed easily by client tools.",
        "fps": "Internal administrative document importers accepting strictly controlled files in locked subnets.",
        "fns": "Sanitizing filename but saving file into web server root directory configured to execute scripts.",
        "heuristics": "Flag any file write operation using `file.filename` directly without UUID generation or path sanitization.",
        "confidence": "high", "reasoning": "Inspect file upload target path construction and check if filename is generated via UUID.",
        "remediation": "Rename all uploads with UUIDs, restrict allowed extensions, and store files outside public web root."
    },
    # V13 API & Web Service
    {
        "subfolder": "v13_api_web_service",
        "req_id": "V13.1.1",
        "title": "API Token Signature & Payload Validation",
        "chapter": "V13 API & Web Service",
        "severity": "critical", "priority": "high", "cwe": "CWE-347", "top10": "A02:2021-Cryptographic Failures",
        "cheat_sheet": "REST_Security_Cheat_Sheet", "wstg": "WSTG-ATHN-04",
        "overview": "Verify that API authentication tokens (JWT) enforce cryptographic signature verification and payload schema validation.",
        "objective": "Ensure API bearer tokens validate signature integrity and payload claims.",
        "why": "Unverified JWT tokens allow attackers to tamper with claim values and bypass authorization.",
        "threat_model": "Attacker modifies JWT payload claim `\"role\": \"user\"` to `\"role\": \"admin\"` and sends request with `\"alg\": \"none\"`.",
        "ast_hints": "ast.Call (jwt.decode, jwt.PyJWT)",
        "regex_hints": r"(?i)jwt\.decode\([^)]*verify_signature\s*=\s*False",
        "semantic_hints": "Decoding JWT tokens without specifying allowed signature algorithms or setting verify_signature=False.",
        "apis": "jwt.decode, jose.jwt.decode", "imports": "import jwt, from jose import jwt",
        "bad_code": "def parse(t): return jwt.decode(t, options={'verify_signature': False})",
        "good_code": "def parse(t): return jwt.decode(t, SECRET_KEY, algorithms=['HS256'])",
        "fastapi": "def get_user(t: str = Depends(oauth2_scheme)):\n    try: return jwt.decode(t, SECRET_KEY, algorithms=['HS256'])\n    except JWTError: raise HTTPException(401)",
        "flask": "@app.before_request\ndef verify_jwt():\n    auth_header = request.headers.get('Authorization')\n    if auth_header: g.user = jwt.decode(auth_header.split(' ')[1], SECRET_KEY, algorithms=['HS256'])",
        "django": "# DRF handles JWT signature validation automatically via rest_framework_simplejwt",
        "sqlalchemy": "# Cache revoked JWT IDs (jti) in Redis / DB revocation table",
        "postgresql": "-- Store revoked JWT jti tokens in revocation list table",
        "mistakes": "Accepting `none` algorithm in JWT decode parameters.",
        "fps": "Parsing public token headers strictly for un-authenticated analytics tracking prior to auth layer.",
        "fns": "Verifying signature but failing to check token expiration `exp` claim.",
        "heuristics": "Flag any `jwt.decode` call where algorithms list is missing or signature verification is disabled.",
        "confidence": "high", "reasoning": "Inspect jwt.decode parameters and flag missing algorithms list or disabled signature verification.",
        "remediation": "Enforce signature verification and pass explicit allowed algorithms list to `jwt.decode()`."
    },
    # V14 Configuration
    {
        "subfolder": "v14_configuration",
        "req_id": "V14.4.1",
        "title": "HTTP Security Headers Configuration",
        "chapter": "V14 Configuration",
        "severity": "medium", "priority": "medium", "cwe": "CWE-1021", "top10": "A05:2021-Security Misconfiguration",
        "cheat_sheet": "HTTP_Headers_Cheat_Sheet", "wstg": "WSTG-CONF-07",
        "overview": "Verify that application responses include mandatory HTTP security headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options).",
        "objective": "Ensure web application sets HTTP security headers to protect users from XSS, clickjacking, and MIME sniffing.",
        "why": "Missing security headers leaves clients vulnerable to cross-site scripting, framing attacks, and SSL downgrade.",
        "threat_model": "Attacker frames target web site in an iframe on a malicious site to perform clickjacking attack.",
        "ast_hints": "ast.Call (add_middleware, Talisman, response.headers)",
        "regex_hints": r"(?i)X-Frame-Options|Content-Security-Policy|Strict-Transport-Security",
        "semantic_hints": "Omitting security header middleware from application setup.",
        "apis": "response.headers, Talisman, SecurityHeadersMiddleware", "imports": "from flask_talisman import Talisman",
        "bad_code": "@app.get('/')\ndef index(): return {'message': 'Hello'}",
        "good_code": "@app.get('/')\ndef index(r: Response):\n    r.headers['X-Frame-Options'] = 'DENY'\n    r.headers['X-Content-Type-Options'] = 'nosniff'\n    return {'message': 'Hello'}",
        "fastapi": "@app.middleware('http')\ndef add_sec_headers(request, call_next):\n    resp = call_next(request)\n    resp.headers['X-Frame-Options'] = 'DENY'\n    return resp",
        "flask": "from flask_talisman import Talisman\nTalisman(app, content_security_policy=None)",
        "django": "SECURE_BROWSER_XSS_FILTER = True\nSECURE_CONTENT_TYPE_NOSNIFF = True\nX_FRAME_OPTIONS = 'DENY'",
        "sqlalchemy": "# Configured at web application or reverse proxy level",
        "postgresql": "-- Configured at web application or load balancer layer",
        "mistakes": "Setting `X-Frame-Options: ALLOWALL` or permissive Content-Security-Policy `default-src *`.",
        "fps": "API-only backend services returning pure JSON without HTML rendering requirements.",
        "fns": "Configuring security headers on application routes but missing them on static asset routes.",
        "heuristics": "Flag web application configurations lacking security header middleware or security settings.",
        "confidence": "high", "reasoning": "Inspect application middleware initialization for security header definitions.",
        "remediation": "Apply centralized security header middleware to enforce CSP, HSTS, X-Content-Type-Options, and X-Frame-Options."
    }
]

WSTG_DATASET = [
    {
        "subfolder": "authentication_testing",
        "test_id": "WSTG-ATHN-01",
        "title": "Testing for Credentials Transported over Encrypted Channels",
        "category": "Authentication Testing",
        "severity": "critical", "priority": "high", "cwe": "CWE-319", "top10": "A02:2021-Cryptographic Failures",
        "cheat_sheet": "Transport_Layer_Security_Cheat_Sheet", "asvs": "V9.1.1",
        "overview": "Verify that all authentication requests and sensitive credentials are submitted exclusively over HTTPS/TLS encrypted channels.",
        "objective": "Identify unencrypted HTTP authentication endpoints and cleartext credential transmission.",
        "why": "Unencrypted HTTP transmissions allow attackers on local networks to sniff credentials and session tokens.",
        "threat_model": "Attacker performs ARP spoofing or Wi-Fi eavesdropping to intercept cleartext POST request containing username and password.",
        "ast_hints": "ast.Call (redirect, set_cookie), ast.Assign (SERVER_SSL, HTTP_PORT)",
        "regex_hints": r"(?i)(http://|allow_insecure|SSL=False)",
        "semantic_hints": "Configuration or route definitions allowing non-TLS connections for authentication endpoints.",
        "apis": "ssl.wrap_socket, HTTPSRedirectMiddleware", "imports": "from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware",
        "bad_code": "app.run(host='0.0.0.0', port=80)",
        "good_code": "app.add_middleware(HTTPSRedirectMiddleware)",
        "fastapi": "app.add_middleware(HTTPSRedirectMiddleware)",
        "flask": "from flask_talisman import Talisman\nTalisman(app, force_https=True)",
        "django": "SECURE_SSL_REDIRECT = True\nSECURE_HSTS_SECONDS = 31536000",
        "sqlalchemy": "engine = create_engine('postgresql://user:pass@db:5432/app?sslmode=require')",
        "postgresql": "ssl = on\nssl_cert_file = '/etc/ssl/certs/server.crt'",
        "mistakes": "Relying on client-side JavaScript to encrypt passwords prior to sending them over HTTP.",
        "fps": "Internal microservices running within an encrypted service mesh (e.g. Istio mTLS).",
        "fns": "Redirection from HTTP to HTTPS occurring after credential POST body has already been submitted in cleartext.",
        "heuristics": "Flag any web server setup missing HTTPS redirection or HSTS headers on auth routes.",
        "confidence": "high", "reasoning": "Inspect web server routing and middleware configuration for HSTS headers and SSL redirect enforcement.",
        "remediation": "Enforce HTTP-to-HTTPS redirect middleware, apply HSTS headers, and configure TLS 1.2+ certificates."
    },
    {
        "subfolder": "authorization_testing",
        "test_id": "WSTG-ATHZ-04",
        "title": "Testing for Insecure Direct Object References (IDOR)",
        "category": "Authorization Testing",
        "severity": "critical", "priority": "high", "cwe": "CWE-639", "top10": "A01:2021-Broken Access Control",
        "cheat_sheet": "Authorization_Cheat_Sheet", "asvs": "V4.2.1",
        "overview": "Verify that user-supplied object keys cannot be manipulated to access unauthorized resources.",
        "objective": "Identify endpoints where changing record identifiers returns records belonging to other users.",
        "why": "IDOR allows attackers to harvest or modify all records in a database by enumerating sequential IDs.",
        "threat_model": "Attacker changes URL `/api/user/101/invoice` to `/api/user/102/invoice` to view another user's invoice.",
        "ast_hints": "ast.FunctionDef, ast.Call (filter, get, query)",
        "regex_hints": r"(?i)filter_by\(id\s*=\s*\w+\)(?!\.filter\(.*user_id)",
        "semantic_hints": "Fetching records using user-supplied ID parameters without scoping the query to active user ID.",
        "apis": "db.session.query, filter, get_object_or_404", "imports": "from django.shortcuts import get_object_or_404",
        "bad_code": "@app.get('/invoice/{id}')\ndef get_invoice(id: int): return db.query(Invoice).get(id)",
        "good_code": "@app.get('/invoice/{id}')\ndef get_invoice(id: int, user=Depends(get_current_user)):\n    inv = db.query(Invoice).filter(Invoice.id == id, Invoice.user_id == user.id).first()\n    if not inv: raise HTTPException(404)\n    return inv",
        "fastapi": "@app.get('/doc/{id}')\ndef read_doc(id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):\n    doc = db.query(Document).filter(Document.id == id, Document.user_id == user.id).first()\n    if not doc: raise HTTPException(404)\n    return doc",
        "flask": "@app.route('/doc/<id>')\n@login_required\ndef read_doc(id):\n    doc = Document.query.filter_by(id=id, user_id=current_user.id).first_or_404()\n    return jsonify(doc.to_dict())",
        "django": "def read_doc(request, id):\n    doc = get_object_or_404(Document, id=id, owner=request.user)\n    return JsonResponse({'title': doc.title})",
        "sqlalchemy": "query = session.query(Order).filter(Order.id == order_id, Order.user_id == current_user_id)",
        "postgresql": "CREATE POLICY user_orders_policy ON orders FOR ALL USING (user_id = current_setting('app.current_user_id')::int);",
        "mistakes": "Relying on GUID complexity alone without verifying ownership on backend queries.",
        "fps": "Endpoints serving public un-restricted resources (e.g. public blog posts).",
        "fns": "Checking permissions on GET requests but forgetting to apply owner filters on PUT/DELETE routes.",
        "heuristics": "Flag any route taking an ID parameter where database query does not filter by active user/tenant ID.",
        "confidence": "high", "reasoning": "Identify route accepting resource ID, trace database lookup logic, and check for user ownership filter.",
        "remediation": "Scope all database queries to include active user/tenant ownership filters."
    },
    {
        "subfolder": "input_validation",
        "test_id": "WSTG-INPV-05",
        "title": "Testing for SQL Injection",
        "category": "Input Validation Testing",
        "severity": "critical", "priority": "high", "cwe": "CWE-89", "top10": "A03:2021-Injection",
        "cheat_sheet": "SQL_Injection_Prevention_Cheat_Sheet", "asvs": "V5.3.1",
        "overview": "Verify that user-supplied input passed into database operations cannot alter the structure of SQL queries.",
        "objective": "Detect SQL injection vulnerabilities in database access logic across all user input channels.",
        "why": "SQL Injection enables unauthorized administrative bypass, data exfiltration, and database corruption.",
        "threat_model": "Attacker supplies `' UNION SELECT username, password_hash FROM users--` in search field to steal credentials.",
        "ast_hints": "ast.Call (execute, raw), ast.JoinedStr, ast.BinOp (Mod, Add)",
        "regex_hints": r"(?i)\.execute\(\s*f['\"].*SELECT",
        "semantic_hints": "String interpolation or concatenation used to build SQL query strings.",
        "apis": "db.session.execute, text(), cursor.execute", "imports": "from sqlalchemy import text, import sqlite3",
        "bad_code": "def search(term): return db.execute(f\"SELECT * FROM users WHERE name LIKE '%{term}%'\")",
        "good_code": "def search(term): return db.execute(text(\"SELECT * FROM users WHERE name LIKE :t\"), {\"t\": f\"%{term}%\"})",
        "fastapi": "@app.get('/search')\ndef search(q: str, db: Session = Depends(get_db)):\n    return db.query(User).filter(User.username.contains(q)).all()",
        "flask": "@app.route('/search')\ndef search():\n    q = request.args.get('q', '')\n    return jsonify([u.to_dict() for u in User.query.filter(User.username.like(f'%{q}%')).all()])",
        "django": "def search(request):\n    q = request.GET.get('q', '')\n    return JsonResponse(list(User.objects.filter(username__icontains=q).values()), safe=False)",
        "sqlalchemy": "session.query(User).filter(User.username == search_term)",
        "postgresql": "SELECT * FROM users WHERE username = $1;",
        "mistakes": "Attempting to sanitize input by stripping quotes instead of using parameterization.",
        "fps": "Using f-strings to format table or column names when validated strictly against an internal static whitelist.",
        "fns": "Using ORM methods like `raw()` or `extra()` with unsanitized string formatting.",
        "heuristics": "Flag any dynamic SQL string construction passed directly to execution sinks.",
        "confidence": "high", "reasoning": "Scan for DB execution sinks and flag dynamic SQL string construction.",
        "remediation": "Use parameterized queries or standard ORM abstractions exclusively for all database interactions."
    },
    {
        "subfolder": "input_validation",
        "test_id": "WSTG-INPV-19",
        "title": "Testing for Server-Side Request Forgery (SSRF)",
        "category": "Input Validation Testing",
        "severity": "high", "priority": "high", "cwe": "CWE-918", "top10": "A10:2021-Server-Side Request Forgery",
        "cheat_sheet": "Server_Side_Request_Forgery_Prevention_Cheat_Sheet", "asvs": "V12.6.1",
        "overview": "Verify that user-supplied URLs or network targets fetched by the server are restricted to validated allowlists.",
        "objective": "Identify endpoints where server fetches user-controlled URLs without resolving IP ranges or restricting internal subnets.",
        "why": "SSRF enables attackers to scan internal networks, query local services, and access cloud metadata APIs.",
        "threat_model": "Attacker submits `http://169.254.169.254/latest/meta-data/` to steal AWS IAM credentials.",
        "ast_hints": "ast.Call (requests.get, urllib.request.urlopen, httpx.get)",
        "regex_hints": r"(?i)(requests|httpx|urllib)\.(get|post|request)\(\s*\w+",
        "semantic_hints": "Passing user-controlled URL string directly to outbound HTTP clients without hostname allowlisting.",
        "apis": "requests.get, httpx.AsyncClient, urllib.request.urlopen", "imports": "import requests, import httpx, from urllib.parse import urlparse",
        "bad_code": "@app.post('/fetch')\ndef fetch_url(url: str): return requests.get(url).content",
        "good_code": "ALLOWED = {'cdn.example.com'}\ndef fetch_url(url: str):\n    p = urlparse(url)\n    if p.scheme != 'https' or p.netloc not in ALLOWED: raise ValueError('Denied')\n    return requests.get(url, timeout=5).content",
        "fastapi": "@app.post('/webhook')\ndef reg_webhook(url: HttpUrl):\n    p = urlparse(str(url))\n    if p.hostname in ('localhost', '127.0.0.1', '169.254.169.254'): raise HTTPException(400)\n    return {'status': 'ok'}",
        "flask": "@app.route('/fetch')\ndef fetch():\n    u = request.args.get('url')\n    if urlparse(u).netloc not in ALLOWED: abort(400)\n    return requests.get(u, timeout=3).content",
        "django": "def fetch(request):\n    u = request.GET.get('url')\n    if not is_safe_url(u): return HttpResponseBadRequest()\n    return HttpResponse(requests.get(u).content)",
        "sqlalchemy": "# Store approved webhook domain configurations in database table",
        "postgresql": "-- Maintain allowlist of remote webhooks in PostgreSQL lookup table",
        "mistakes": "Blacklisting `localhost` while failing to block IPv6 `::1` or decimal IP notation `2130706433`.",
        "fps": "Outbound API calls to hardcoded static third-party integrations (e.g. Stripe API).",
        "fns": "Validating hostname but following HTTP 302 redirects to internal IP addresses.",
        "heuristics": "Flag any outbound HTTP request using a variable URL parameter without domain validation.",
        "confidence": "high", "reasoning": "Locate outbound HTTP client calls and check for domain allowlist and DNS resolution checks.",
        "remediation": "Enforce strict domain allowlists, resolve DNS to verify IPs are not in private ranges, and disable HTTP redirects."
    }
]

# Generate ASVS Markdown Files
for item in ASVS_DATASET:
    item = sanitize_item(item, "asvs")
    filename = f"{item['req_id']}.md"
    file_path = os.path.join(ASVS_DIR, item['subfolder'], filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    fm = f"""---
knowledge_id: ASVS-{item['req_id'].replace('.', '-')}
embedding_title: {item['title']} - OWASP ASVS {item['req_id']} Verification
official_id: {item['req_id']}
document_type: asvs_requirement
chunk_type: concept_and_detection
language:
  - python
frameworks:
  - fastapi
  - flask
  - django
database:
  - sqlalchemy
  - postgresql
retrieval_priority: {item['priority']}
source_version: 4.0.3
confidence: official
severity: {item['severity']}
category: security
subcategory: owasp_asvs
source: OWASP Application Security Verification Standard 4.0.3
canonical_url: https://owasp.org/www-project-application-security-verification-standard/
tags:
  - asvs
  - {item['req_id'].split('.')[0].lower()}
  - {item['cwe'].lower()}
keywords:
  - {item['title'].lower()}
  - {item['cwe'].lower()}
  - asvs {item['req_id']}
aliases:
  - ASVS-{item['req_id']}
  - {item['title']}
related_topics:
  - {item['top10']}
  - {item['cwe']}
related_documents:
  - {item['wstg']}
last_updated: 2026-07-24
---
"""
    
    body = f"""
# Retrieval Summary
OWASP ASVS {item['req_id']} requires {item['title'].lower()}. This verification rule ensures applications enforce {item['objective'].lower()} to prevent {item['why'].lower()} across Python web frameworks including FastAPI, Flask, and Django.

# Overview
{item['overview']}

# Official Requirement
Verify that the application complies with OWASP ASVS {item['req_id']} ({item['chapter']}): {item['overview']}

# Security Objective
{item['objective']}

# Why This Matters
{item['why']}

# Threat Model
{item['threat_model']}

# Detection Guidance
AI code reviewers should scan Python source files for unvalidated usage of {item['apis']}. Look for missing authorization, improper type checking, or un-parameterized dynamic input.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`. Scan function definitions and calls matching these nodes.

# Regex / Search Hints
Use regex pattern: `{item['regex_hints']}` to flag candidate vulnerabilities.

# Semantic Detection Hints
{item['semantic_hints']}

# Relevant Python APIs
`{item['apis']}`

# Relevant Imports
`{item['imports']}`

# Vulnerable Patterns
Insecure implementation exposing security flaws:
```python
{item['bad_code']}
```

# Secure Patterns
Secure implementation fulfilling ASVS {item['req_id']}:
```python
{item['good_code']}
```

# Python Example
```python
{item['good_code']}
```

# FastAPI Example
```python
{item['fastapi']}
```

# Flask Example
```python
{item['flask']}
```

# Django Example
```python
{item['django']}
```

# SQLAlchemy Considerations
{item['sqlalchemy']}

# PostgreSQL Considerations
```sql
{item['postgresql']}
```

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
- [ ] Verify requirement ASVS {item['req_id']} is enforced in code.
- [ ] Confirm automated unit tests validate this constraint.
- [ ] Ensure secure default fallback if validation fails.

# Remediation
{item['remediation']}

# Related OWASP Top 10
{item['top10']}

# Related Cheat Sheets
{item['cheat_sheet']}

# Related CWE
{item['cwe']}

# Related CERT Python Rules
IDS01-P. Normalize strings before validating them.

# Related PEPs
PEP 8 -- Style Guide for Python Code

# Related Security Patterns
Defense in Depth, Fail Securely, Least Privilege.

# Related Anti-Patterns
Security through Obscurity, Hardcoded Credentials, Trusting Untrusted Input.

# Related Repository Rules
Rule-SEC-01: All endpoints must enforce access control and input validation.

# Related WSTG Tests
{item['wstg']}

# References
1. OWASP ASVS Project: https://owasp.org/www-project-application-security-verification-standard/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/{item['cwe'].replace('CWE-', '')}.html
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated ASVS document: {file_path}")

# Generate WSTG Markdown Files
for item in WSTG_DATASET:
    item = sanitize_item(item, "wstg")
    filename = f"{item['test_id']}.md"
    file_path = os.path.join(WSTG_DIR, item['subfolder'], filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    fm = f"""---
knowledge_id: WSTG-{item['test_id'].replace('-', '_')}
embedding_title: {item['title']} - OWASP WSTG {item['test_id']}
official_id: {item['test_id']}
document_type: wstg_test
chunk_type: concept_and_detection
language:
  - python
frameworks:
  - fastapi
  - flask
  - django
database:
  - sqlalchemy
  - postgresql
retrieval_priority: {item['priority']}
source_version: 4.2
confidence: official
severity: {item['severity']}
category: security
subcategory: owasp_wstg
source: OWASP Web Security Testing Guide v4.2
canonical_url: https://owasp.org/www-project-web-security-testing-guide/
tags:
  - wstg
  - {item['test_id'].split('-')[1].lower()}
  - {item['cwe'].lower()}
keywords:
  - {item['title'].lower()}
  - {item['cwe'].lower()}
  - wstg {item['test_id']}
aliases:
  - WSTG-{item['test_id']}
  - {item['title']}
related_topics:
  - {item['top10']}
  - {item['cwe']}
related_documents:
  - {item['asvs']}
last_updated: 2026-07-24
---
"""
    
    body = f"""
# Retrieval Summary
OWASP WSTG {item['test_id']} tests for {item['title'].lower()}. This test methodology evaluates applications to ensure {item['objective'].lower()} and prevents {item['why'].lower()} across Python web applications.

# Overview
{item['overview']}

# Official Test
Execute OWASP WSTG test {item['test_id']} ({item['category']}): {item['overview']}

# Security Objective
{item['objective']}

# Why This Matters
{item['why']}

# Threat Model
{item['threat_model']}

# Detection Guidance
AI code reviewers should evaluate code paths for un-sanitized call flows using {item['apis']}. Verify whether defense controls prevent unauthorized actions.

# AST Detection Hints
Target AST nodes: `{item['ast_hints']}`.

# Regex / Search Hints
Use regex pattern: `{item['regex_hints']}` to discover vulnerable candidates.

# Semantic Detection Hints
{item['semantic_hints']}

# Relevant Python APIs
`{item['apis']}`

# Relevant Imports
`{item['imports']}`

# Vulnerable Patterns
Insecure pattern vulnerable to WSTG {item['test_id']}:
```python
{item['bad_code']}
```

# Secure Patterns
Secure implementation satisfying WSTG {item['test_id']}:
```python
{item['good_code']}
```

# Python Example
```python
{item['good_code']}
```

# FastAPI Example
```python
{item['fastapi']}
```

# Flask Example
```python
{item['flask']}
```

# Django Example
```python
{item['django']}
```

# SQLAlchemy Considerations
{item['sqlalchemy']}

# PostgreSQL Considerations
```sql
{item['postgresql']}
```

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
- [ ] Execute test procedures for WSTG {item['test_id']}.
- [ ] Confirm automated security unit tests cover this scenario.
- [ ] Ensure findings are documented and remediated.

# Remediation
{item['remediation']}

# Related OWASP Top 10
{item['top10']}

# Related Cheat Sheets
{item['cheat_sheet']}

# Related CWE
{item['cwe']}

# Related CERT Python Rules
IDS01-P. Normalize strings before validating them.

# Related PEPs
PEP 8 -- Style Guide for Python Code

# Related Security Patterns
Input Validation, Sanitization, Least Privilege.

# Related Anti-Patterns
Bypassing Controls, Insufficient Logging, Trusting Client State.

# Related Repository Rules
Rule-SEC-02: Ensure all input interfaces and authentication endpoints pass security verification.

# Related ASVS Requirements
{item['asvs']}

# References
1. OWASP WSTG Project: https://owasp.org/www-project-web-security-testing-guide/
2. MITRE CWE: https://cwe.mitre.org/data/definitions/{item['cwe'].replace('CWE-', '')}.html
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    print(f"Generated WSTG document: {file_path}")

print("Builder finished successfully!")
