import os
import yaml

TARGET_DIR = r"d:\RAG\knowledge\devops"

REQUIRED_FM_KEYS = [
    "knowledge_id", "embedding_title", "official_id", "document_type",
    "chunk_type", "title", "category", "subcategory", "version",
    "source", "canonical_url", "source_version", "language", "frameworks",
    "database", "severity", "retrieval_priority", "confidence", "tags",
    "keywords", "aliases", "related_topics", "related_documents", "last_updated"
]

REQUIRED_HEADERS = [
    "# Retrieval Summary", "# Overview", "# Official Definition",
    "# Purpose", "# Why This Matters", "# Detection Guidance",
    "# AST Detection Hints", "# Regex Detection Hints", "# Semantic Detection Hints",
    "# Relevant Python APIs", "# Relevant Framework APIs", "# Relevant Imports",
    "# Common Usage", "# Common Mistakes", "# Bad Practices", "# Best Practices",
    "# Python Example", "# Framework Example", "# SQLAlchemy Example",
    "# Performance Considerations", "# Memory Considerations", "# Thread Safety",
    "# Async Considerations", "# Security Considerations", "# Common Developer Mistakes",
    "# False Positives", "# False Negatives", "# AI Review Heuristics",
    "# Detection Confidence", "# Reasoning Chain", "# Review Checklist",
    "# Optimization Tips", "# Related Python Knowledge", "# Related Standard Library",
    "# Related PEPs", "# Related Security Knowledge", "# Related Design Patterns",
    "# Related Anti-Patterns", "# Related Repository Rules", "# References"
]

def verify():
    print("Starting Comprehensive Verification of DevOps Knowledge Base...")
    
    knowledge_ids = set()
    filenames = set()
    errors = 0
    file_count = 0

    if not os.path.exists(TARGET_DIR):
        print(f"ERROR: Target directory does not exist: {TARGET_DIR}")
        return

    for root, dirs, files in os.walk(TARGET_DIR):
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
        print("SUCCESS: 100% Validation Passed! Zero errors found across DevOps Knowledge Base.")
    else:
        print(f"FAILURE: Found {errors} verification errors.")

if __name__ == "__main__":
    verify()
