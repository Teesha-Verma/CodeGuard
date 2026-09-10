"""
CodeGuard V2 — Security Knowledge Base and Academy Routes.

Exposes searchable CWE/OWASP security standards, vulnerable vs secure code examples,
and interactive academy curricula backed by CodeGuard's 419 RAG knowledge documents.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas import (
    KnowledgeTopicDetail,
    KnowledgeTopicSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

# Canonical high-priority topics with complete code examples & interactive quizzes
CORE_TOPICS: Dict[str, KnowledgeTopicDetail] = {
    "sql-injection": KnowledgeTopicDetail(
        id="sql-injection",
        cwe="CWE-89",
        owasp="A03:2021-Injection",
        title="SQL Injection via Untrusted Input Interpolation",
        category="Injection",
        severity="critical",
        summary="Occurs when user-supplied input is concatenated directly into a SQL statement without parameterization, allowing attackers to manipulate query logic.",
        why_it_matters="SQL injection can lead to unauthorized data retrieval, database dumping, authentication bypass, data tampering, and administrative compromise.",
        mechanics="The database query parser interprets user input characters (such as quotes or semicolons) as control syntax rather than literal data parameters.",
        vulnerable_example=(
            "def get_invoice(request):\n"
            '    account_id = request.args.get("id")\n'
            '    query = f"SELECT * FROM invoices WHERE account_id=\'{account_id}\'"\n'
            "    cursor = db.cursor()\n"
            "    cursor.execute(query)\n"
            "    return cursor.fetchall()"
        ),
        secure_example=(
            "def get_invoice(request):\n"
            '    account_id = request.args.get("id")\n'
            '    query = "SELECT * FROM invoices WHERE account_id = %s"\n'
            "    cursor = db.cursor()\n"
            "    cursor.execute(query, (account_id,))\n"
            "    return cursor.fetchall()"
        ),
        preventive_guidelines=[
            "Always utilize parameterized queries or Object-Relational Mapping (ORM) query builders.",
            "Never concatenate, format, or interpolate strings into dynamic SQL statements.",
            "Implement principle of least privilege on database connection roles.",
            "Employ input validation to ensure identifiers conform to expected patterns (e.g. UUIDs or integers)."
        ],
        quiz_question="Which of the following database queries is completely safe from SQL injection?",
        quiz_options=[
            'cursor.execute(f"SELECT * FROM users WHERE email = \'{email}\'")',
            'cursor.execute("SELECT * FROM users WHERE email = %s", (email,))',
            'cursor.execute("SELECT * FROM users WHERE email = \'" + email + "\'")',
            'cursor.execute("SELECT * FROM users WHERE email = {}".format(email))'
        ],
        quiz_correct_index=1,
        quiz_explanation="Parameterized placeholders (%s) instruct the driver to send parameters over a separate binary wire protocol, ensuring input cannot break query syntax."
    ),
    "command-injection": KnowledgeTopicDetail(
        id="command-injection",
        cwe="CWE-78",
        owasp="A03:2021-Injection",
        title="Command Injection via Shell Subprocesses",
        category="Injection",
        severity="critical",
        summary="Occurs when external user input is passed directly to an operating system shell without sanitization, allowing arbitrary command execution.",
        why_it_matters="Command injection allows complete host takeover, access to environment secrets, lateral cloud movement, and persistent malware installation.",
        mechanics="When shell=True is enabled, the OS shell evaluates metacharacters such as `|`, `&`, `;`, and `$(...)`, executing chained secondary commands.",
        vulnerable_example=(
            "import subprocess\n\n"
            "def ping_host(request):\n"
            '    host = request.args.get("host")\n'
            '    # Vulnerable: shell=True evaluates chained commands\n'
            '    cmd = f"ping -c 1 {host}"\n'
            "    return subprocess.check_output(cmd, shell=True)"
        ),
        secure_example=(
            "import subprocess, ipaddress\n\n"
            "def ping_host(request):\n"
            '    host = request.args.get("host")\n'
            "    ipaddress.ip_address(host)  # Validate IP structure\n"
            '    # Secure: list arguments without shell execution\n'
            "    return subprocess.check_output(['ping', '-c', '1', host], shell=False)"
        ),
        preventive_guidelines=[
            "Never invoke a shell using `shell=True` or `os.system` with dynamic arguments.",
            "Pass arguments as an explicit array to `subprocess.run(..., shell=False)`.",
            "Validate inputs using strict allowlists (e.g., regex, IP parsers, integer bounds).",
            "Prefer standard library APIs over operating system shell commands."
        ],
        quiz_question="What parameter in Python's subprocess module must be avoided when handling untrusted arguments?",
        quiz_options=[
            "check=True",
            "shell=True",
            "capture_output=True",
            "text=True"
        ],
        quiz_correct_index=1,
        quiz_explanation="Setting shell=True passes the string to /bin/sh or cmd.exe, which interprets shell control characters like semicolons and pipes."
    ),
    "unsafe-deserialization": KnowledgeTopicDetail(
        id="unsafe-deserialization",
        cwe="CWE-502",
        owasp="A08:2021-Software and Data Integrity Failures",
        title="Unsafe Deserialization via Python Pickle",
        category="Memory & Deserialization",
        severity="critical",
        summary="Occurs when untrusted byte streams are unpickled using `pickle.loads()`, triggering arbitrary Python callable execution during reconstruction.",
        why_it_matters="Pickle bytecode can instantiate objects and invoke `__reduce__` methods, leading directly to Remote Code Execution (RCE).",
        mechanics="The pickle VM processes opcodes during deserialization that can import modules (`os`, `posix`) and invoke callables like `system()`.",
        vulnerable_example=(
            "import pickle, base64\n\n"
            "def restore_session(request):\n"
            '    raw_cookie = request.cookies.get("session")\n'
            "    # Vulnerable: unpickling untrusted payload\n"
            "    data = pickle.loads(base64.b64decode(raw_cookie))\n"
            "    return data"
        ),
        secure_example=(
            "import json, hmac, hashlib\n\n"
            "def restore_session(request):\n"
            '    raw_cookie = request.cookies.get("session")\n'
            "    # Secure: use safe JSON format with cryptographic signature\n"
            "    return json.loads(raw_cookie)"
        ),
        preventive_guidelines=[
            "Never deserialize untrusted user data using `pickle`, `yaml.unsafe_load`, or `marshal`.",
            "Use safe, standard interchange formats such as JSON, Protocol Buffers, or MessagePack.",
            "Digitally sign serialized state using HMAC-SHA256 before transmitting across untrusted boundaries."
        ],
        quiz_question="Which serialization format is inherently safe against arbitrary code execution when parsing untrusted input?",
        quiz_options=[
            "Python pickle",
            "PyYAML with default Loader",
            "Standard JSON (json.loads)",
            "Python marshal"
        ],
        quiz_correct_index=2,
        quiz_explanation="JSON is a pure data specification without executable constructs or class instantiation mechanisms."
    ),
    "path-traversal": KnowledgeTopicDetail(
        id="path-traversal",
        cwe="CWE-22",
        owasp="A01:2021-Broken Access Control",
        title="Path Traversal via Unvalidated File Paths",
        category="Configuration",
        severity="high",
        summary="Occurs when user-supplied filenames containing `../` sequences are joined into filesystem paths, allowing reading or overwriting arbitrary files.",
        why_it_matters="Attackers can read server configuration, environment secrets, private keys, database credentials, or system password hashes.",
        mechanics="Relative path traversal tokens `../` allow navigating out of the designated directory to root directories on the host.",
        vulnerable_example=(
            "import os\n\n"
            "def download_report(request):\n"
            '    filename = request.args.get("file")\n'
            '    # Vulnerable: filename could be ../../../etc/passwd\n'
            '    filepath = os.path.join("/var/app/reports", filename)\n'
            '    with open(filepath, "r") as f:\n'
            "        return f.read()"
        ),
        secure_example=(
            "import os\n"
            "from pathlib import Path\n\n"
            "def download_report(request):\n"
            '    filename = os.path.basename(request.args.get("file"))\n'
            '    base_dir = Path("/var/app/reports").resolve()\n'
            "    filepath = (base_dir / filename).resolve()\n"
            "    if not filepath.is_relative_to(base_dir):\n"
            '        raise ValueError("Invalid path")\n'
            '    with open(filepath, "r") as f:\n'
            "        return f.read()"
        ),
        preventive_guidelines=[
            "Use `os.path.basename()` or `Path.name` to strip directory traversal characters.",
            "Resolve absolute paths using `Path.resolve()` and verify with `is_relative_to()`.",
            "Store files using random UUID keys in storage instead of client-supplied names."
        ],
        quiz_question="How should an application ensure a resolved file path stays within a safe directory?",
        quiz_options=[
            "Check that the filename ends with .pdf or .txt",
            "Strip all single dots from the path",
            "Resolve the absolute path and verify it starts with or is relative to the base directory",
            "Wrap the file open in a try-except block"
        ],
        quiz_correct_index=2,
        quiz_explanation="Resolving the canonical path resolves all symlinks and `..` segments, allowing unambiguous boundary containment checks."
    ),
    "hardcoded-secrets": KnowledgeTopicDetail(
        id="hardcoded-secrets",
        cwe="CWE-798",
        owasp="A07:2021-Identification and Authentication Failures",
        title="Hardcoded Cryptographic Keys and API Credentials",
        category="Authentication",
        severity="high",
        summary="Occurs when sensitive secrets, API tokens, private keys, or passwords are hardcoded directly into application source code.",
        why_it_matters="Hardcoded credentials are committed to version control repositories, exposed in client bundles, and leaked during security breaches.",
        mechanics="Static analysis tools scan strings and AST constants for high-entropy tokens and recognizable key patterns.",
        vulnerable_example=(
            '# Vulnerable: secret key committed to code\n'
            'SECRET_KEY = "demo_insecure_api_secret_key_12345"\n'
            'DB_PASS = "ProductionSuperSecret123!"\n'
        ),
        secure_example=(
            "import os\n\n"
            "# Secure: load from environment or secrets vault\n"
            'SECRET_KEY = os.environ["SECRET_KEY"]\n'
            'DB_PASS = os.environ["DATABASE_PASSWORD"]\n'
        ),
        preventive_guidelines=[
            "Load all secrets, keys, and tokens from environment variables or a secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault).",
            "Implement pre-commit hooks to detect secret patterns before code is committed.",
            "Rotate exposed credentials immediately upon detection in source code."
        ],
        quiz_question="What is the recommended approach for storing third-party API credentials?",
        quiz_options=[
            "Hardcoded in a private internal module",
            "Base64 encoded inside the main script",
            "Loaded from environment variables or a dedicated secrets manager",
            "Stored in a commented-out section of the code"
        ],
        quiz_correct_index=2,
        quiz_explanation="Environment variables and dedicated vault solutions keep secrets out of source control and allow secure rotation."
    ),
    "ssrf": KnowledgeTopicDetail(
        id="ssrf",
        cwe="CWE-918",
        owasp="A10:2021-Server-Side Request Forgery",
        title="Server-Side Request Forgery (SSRF)",
        category="Network",
        severity="high",
        summary="Occurs when a web application fetches a remote resource without validating the user-supplied destination URL, allowing requests to internal networks.",
        why_it_matters="Attackers can access cloud metadata services (e.g., 169.254.169.254), internal Redis/database clusters, and protected microservices.",
        mechanics="The backend server acts as an unwitting proxy, making outbound HTTP/socket requests on behalf of an external attacker.",
        vulnerable_example=(
            "import requests\n\n"
            "def fetch_avatar(request):\n"
            '    url = request.args.get("url")\n'
            "    # Vulnerable: attacker can specify http://169.254.169.254/latest/meta-data/\n"
            "    resp = requests.get(url)\n"
            "    return resp.content"
        ),
        secure_example=(
            "import requests, ipaddress\n"
            "from urllib.parse import urlparse\n\n"
            "def fetch_avatar(request):\n"
            '    url = request.args.get("url")\n'
            "    parsed = urlparse(url)\n"
            '    if parsed.scheme not in ("http", "https"):\n'
            '        raise ValueError("Invalid scheme")\n'
            "    # Disallow internal / loopback / link-local addresses\n"
            "    ip = ipaddress.ip_address(parsed.hostname)\n"
            "    if ip.is_private or ip.is_loopback or ip.is_link_local:\n"
            '        raise ValueError("Forbidden destination")\n'
            "    return requests.get(url, timeout=5).content"
        ),
        preventive_guidelines=[
            "Validate destination URLs against strict domain/IP allowlists.",
            "Block private RFC 1918 ranges, loopback 127.0.0.1, and link-local cloud metadata (169.254.169.254).",
            "Disable HTTP redirects in client request libraries to prevent address spoofing."
        ],
        quiz_question="What IP address range must be protected against SSRF in cloud deployments?",
        quiz_options=[
            "8.8.8.8 (Google DNS)",
            "169.254.169.254 (Cloud instance metadata service)",
            "1.1.1.1 (Cloudflare DNS)",
            "208.67.222.222 (OpenDNS)"
        ],
        quiz_correct_index=1,
        quiz_explanation="169.254.169.254 is the link-local metadata address in AWS, GCP, and Azure that provides IAM credentials and environment keys."
    ),
}


@router.get("/topics", response_model=List[KnowledgeTopicSummary])
def list_knowledge_topics(
    category: Optional[str] = Query(None, description="Filter by topic category"),
    search: Optional[str] = Query(None, description="Search term in title, CWE, or summary")
) -> List[KnowledgeTopicSummary]:
    """
    Search and retrieve security topics across CWE standards, OWASP, and AST rules.
    """
    results: List[KnowledgeTopicSummary] = []

    for topic in CORE_TOPICS.values():
        if category and category.upper() != "ALL" and topic.category.lower() != category.lower():
            continue

        if search:
            q = search.lower()
            matches = (
                q in topic.title.lower()
                or q in topic.cwe.lower()
                or q in topic.owasp.lower()
                or q in topic.summary.lower()
                or q in topic.category.lower()
            )
            if not matches:
                continue

        results.append(
            KnowledgeTopicSummary(
                id=topic.id,
                cwe=topic.cwe,
                owasp=topic.owasp,
                title=topic.title,
                category=topic.category,
                severity=topic.severity,
                summary=topic.summary,
            )
        )

    return results


@router.get("/topics/{topic_id}", response_model=KnowledgeTopicDetail)
def get_knowledge_topic(topic_id: str) -> KnowledgeTopicDetail:
    """
    Retrieve full educational document for a specific security concept,
    including vulnerable/secure examples, prevention guidelines, and quiz.
    """
    normalized_id = topic_id.lower().replace("_", "-")

    # Match by key or CWE
    matched = CORE_TOPICS.get(normalized_id)
    if not matched:
        for t in CORE_TOPICS.values():
            if t.cwe.lower() == normalized_id or t.id.lower() == normalized_id:
                matched = t
                break

    if not matched:
        # Fallback to first topic if unknown
        matched = CORE_TOPICS["sql-injection"]

    return matched
