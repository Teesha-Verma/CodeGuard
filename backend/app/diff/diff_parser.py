import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ChangedLine:
    line_number: int
    content: str
    is_added: bool
    is_removed: bool

@dataclass
class DiffHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[ChangedLine] = field(default_factory=list)

@dataclass
class DiffFile:
    file_path: str
    old_file_path: Optional[str] = None
    is_new: bool = False
    is_deleted: bool = False
    is_rename: bool = False
    hunks: List[DiffHunk] = field(default_factory=list)
    added_lines: List[int] = field(default_factory=list)
    removed_lines: List[int] = field(default_factory=list)

class DiffParser:
    """Parses raw git diffs into structured dataclasses representing files, hunks, and lines."""
    
    HUNK_PATTERN = re.compile(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")

    def parse(self, diff_text: str) -> List[DiffFile]:
        files: List[DiffFile] = []
        current_file: Optional[DiffFile] = None
        current_hunk: Optional[DiffHunk] = None
        
        old_line_no = 0
        new_line_no = 0

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)
                
                parts = line.split(" ")
                old_path = parts[-2].replace("a/", "", 1)
                new_path = parts[-1].replace("b/", "", 1)
                
                current_file = DiffFile(file_path=new_path, old_file_path=old_path)
                if old_path != new_path:
                    current_file.is_rename = True
                current_hunk = None

            elif line.startswith("new file mode"):
                if current_file:
                    current_file.is_new = True
            elif line.startswith("deleted file mode"):
                if current_file:
                    current_file.is_deleted = True
            
            elif line.startswith("@@"):
                match = self.HUNK_PATTERN.search(line)
                if match and current_file:
                    old_start = int(match.group(1))
                    old_lines = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_lines = int(match.group(4)) if match.group(4) else 1
                    
                    current_hunk = DiffHunk(old_start, old_lines, new_start, new_lines)
                    current_file.hunks.append(current_hunk)
                    
                    old_line_no = old_start
                    new_line_no = new_start

            elif line.startswith("-") and not line.startswith("---"):
                if current_hunk:
                    content = line[1:]
                    current_hunk.lines.append(ChangedLine(old_line_no, content, is_added=False, is_removed=True))
                    if current_file:
                        current_file.removed_lines.append(old_line_no)
                    old_line_no += 1

            elif line.startswith("+") and not line.startswith("+++"):
                if current_hunk:
                    content = line[1:]
                    current_hunk.lines.append(ChangedLine(new_line_no, content, is_added=True, is_removed=False))
                    if current_file:
                        current_file.added_lines.append(new_line_no)
                    new_line_no += 1

            elif line.startswith(" ") and current_hunk:
                # Context line
                content = line[1:]
                current_hunk.lines.append(ChangedLine(new_line_no, content, is_added=False, is_removed=False))
                old_line_no += 1
                new_line_no += 1

        if current_file:
            files.append(current_file)

        return files
