import os
import yaml

BASE_DIR = r"d:\RAG\knowledge"

def verify():
    print("Verifying generated Knowledge Base...")
    
    total_files = 0
    md_files = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        if root == BASE_DIR:
            continue
        for file in files:
            if file.endswith(".md"):
                total_files += 1
                md_files.append(os.path.join(root, file))
                
    print(f"Total Markdown files found: {total_files}")
    
    errors = 0
    for file_path in md_files:
        # Check size
        if os.path.getsize(file_path) == 0:
            print(f"ERROR: File is empty: {file_path}")
            errors += 1
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check frontmatter structure
        if not content.startswith("---"):
            print(f"ERROR: Missing frontmatter start delimiter in: {file_path}")
            errors += 1
            continue
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"ERROR: Missing frontmatter end delimiter in: {file_path}")
            errors += 1
            continue
            
        fm_text = parts[1]
        try:
            fm = yaml.safe_load(fm_text)
            required_keys = ["id", "title", "category", "subcategory", "severity", "priority", "tags", "source"]
            for rk in required_keys:
                if rk not in fm:
                    print(f"ERROR: Missing metadata key '{rk}' in: {file_path}")
                    errors += 1
        except Exception as e:
            print(f"ERROR: YAML parsing failed for: {file_path}. Details: {e}")
            errors += 1
            
        # Check required headers
        required_headers = [
            "# Overview",
            "# Why it matters",
            "# Detection Rules",
            "# Bad Code Patterns",
            "# Good Code Patterns",
            "# Common Mistakes",
            "# Secure Alternatives",
            "# Framework Notes",
            "# Performance Considerations",
            "# Related Standards",
            "# References"
        ]
        
        missing_headers = []
        for header in required_headers:
            if header not in content:
                missing_headers.append(header)
                
        if missing_headers:
            print(f"ERROR: Missing headers in {file_path}: {missing_headers}")
            errors += 1
            
    if errors == 0:
        print("SUCCESS: All files successfully validated! No errors found.")
    else:
        print(f"FAILURE: Validation completed with {errors} errors.")

if __name__ == "__main__":
    verify()
