from app.diff.diff_parser import DiffParser
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_diff_parser_parses_files():
    with open(os.path.join(FIXTURES_DIR, "sample_diff.txt"), "r") as f:
        raw_diff = f.read()
    
    parser = DiffParser()
    files = parser.parse(raw_diff)
    
    assert len(files) == 1
    assert files[0].file_path == "utils/helpers.py"

def test_diff_parser_extracts_hunks():
    with open(os.path.join(FIXTURES_DIR, "sample_diff.txt"), "r") as f:
        raw_diff = f.read()
    
    parser = DiffParser()
    files = parser.parse(raw_diff)
    
    assert len(files[0].hunks) >= 1

def test_diff_parser_identifies_added_lines():
    with open(os.path.join(FIXTURES_DIR, "sample_diff.txt"), "r") as f:
        raw_diff = f.read()
    
    parser = DiffParser()
    files = parser.parse(raw_diff)
    
    # Should have detected added lines
    assert len(files[0].added_lines) > 0

def test_diff_parser_empty_input():
    parser = DiffParser()
    files = parser.parse("")
    assert files == []
