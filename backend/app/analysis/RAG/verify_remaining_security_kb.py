import os
import yaml

TARGET_DIRS = [
    r"d:\RAG\knowledge\security\cwe",
    r"d:\RAG\knowledge\security\cert\python",
    r"d:\RAG\knowledge\security\nist",
    r"d:\RAG\knowledge\security\security_patterns",
    r"d:\RAG\knowledge\security\anti_patterns"
]

REQUIRED_FM_KEYS = [
    "knowledge_id", "embedding_title", "official_id", "document_type",
    "chunk_type", "title", "category", "subcategory", "version",
    "source", "canonical_url", "source_version", "language", "frameworks",
    "database", "severity", "retrieval_priority", "confidence", "tags",
    "keywords", "aliases", "related_topics", "related_documents", "last_updated"
]

REQUIRED_HEADERS = [
    "# Retrieval Summary", "# Overview", "# Official Definition",
    "# Security Objective", "# Why This Matters", "# Threat Model",
    "# Detection Guidance", "# AST Detection Hints", "# Regex Detection Hints",
    "# Semantic Detection Hints", "# Relevant Python APIs", "# Relevant Imports",
    "# Vulnerable Patterns", "# Secure Patterns", "# Python Example",
    "# FastAPI Example", "# Flask Example", "# Django Example",
    "# SQLAlchemy Considerations", "# PostgreSQL Considerations",
    "# Common Developer Mistakes", "# False Positives", "# False Negatives",
    "# AI Review Heuristics", "# Detection Confidence", "# Reasoning Chain",
    "# Review Checklist", "# Remediation", "# Related OWASP Top 10",
    "# Related ASVS Requirements", "# Related WSTG Tests", "# Related CWE",
    "# Related CERT Python Rules", "# Related NIST Guidance",
    "# Related Security Patterns", "# Related Anti-Patterns",
    "# Related Repository Rules", "# Related PEPs", "# References"
]

def verify():
    print("Starting Comprehensive Verification of Remaining Security Modules...")
    
    knowledge_ids = set()
    filenames = set()
    errors = 0
    file_count = 0

    for base_dir in TARGET_DIRS:
        if not os.path.exists(base_dir):
            print(f"ERROR: Target directory does not exist: {base_dir}")
            errors += 1
            continue
            
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if not file.endswith(".md"):
                    continue
                file_count += 1
                file_path = os.path.join(root, file)
                
                # Check duplicate filename
                if file in filenames:
                    print(f"ERROR: Duplicate filename found: {file} at {file_path}")
                    errors += 1
                filenames.add(file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Check empty file
                if len(content.strip()) == 0:
                    print(f"ERROR: Empty file: {file_path}")
                    errors += 1
                    continue
                    
                # Check YAML frontmatter
                if not content.startswith("---"):
                    print(f"ERROR: Missing frontmatter start in {file_path}")
                    errors += 1
                    continue
                    
                parts = content.split("---", 2)
                if len(parts) < 3:
                    print(f"ERROR: Missing frontmatter end in {file_path}")
                    errors += 1
                    continue
                    
                fm_raw = parts[1]
                try:
                    fm = yaml.safe_load(fm_raw)
                    # Check mandatory frontmatter keys
                    for key in REQUIRED_FM_KEYS:
                        if key not in fm or fm[key] is None:
                            print(f"ERROR: Missing frontmatter key '{key}' in {file_path}")
                            errors += 1
                            
                    # Check knowledge_id uniqueness
                    kid = fm.get("knowledge_id")
                    if kid:
                        if kid in knowledge_ids:
                            print(f"ERROR: Duplicate knowledge_id '{kid}' in {file_path}")
                            errors += 1
                        knowledge_ids.add(kid)
                except Exception as e:
                    print(f"ERROR: YAML parsing error in {file_path}: {e}")
                    errors += 1
                    
                # Check Markdown Headers
                body = parts[2]
                for h in REQUIRED_HEADERS:
                    if h not in body:
                        print(f"ERROR: Missing header '{h}' in {file_path}")
                        errors += 1
                        
                # Check placeholders
                placeholders = ["TODO", "TBD", "FIXME", "XXX"]
                for ph in placeholders:
                    if ph in body:
                        print(f"ERROR: Found placeholder '{ph}' in {file_path}")
                        errors += 1
                        
                # Check Word Count (Target: 300 - 1200 words)
                words = len(body.split())
                if words < 250:
                    print(f"WARNING/ERROR: Word count too low ({words} words) in {file_path}")
                    errors += 1

    print(f"\nVerification finished! Checked {file_count} Markdown files.")
    if errors == 0:
        print("SUCCESS: 100% Validation Passed! Zero errors found across all remaining security modules.")
    else:
        print(f"FAILURE: Found {errors} verification errors.")

if __name__ == "__main__":
    verify()
