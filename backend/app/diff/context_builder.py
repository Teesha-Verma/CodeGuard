import os
from typing import List, Dict, Any, Optional
from app.diff.diff_parser import DiffFile
from app.core.config import get_settings

class ContextBuilder:
    """Builds a localized code context window around changed lines for LLM grounding."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.settings = get_settings()

    def read_file_lines(self, file_path: str) -> List[str]:
        full_path = os.path.join(self.repo_path, file_path)
        if not os.path.exists(full_path):
            return []
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read().splitlines()
        except Exception:
            return []

    def build_context(self, diff_file: DiffFile) -> Dict[str, Any]:
        """
        Builds localized context for a changed file by expanding the context window
        around changed lines from the actual file on disk.
        """
        if diff_file.is_deleted:
            return {"file_path": diff_file.file_path, "status": "deleted", "snippets": []}

        file_lines = self.read_file_lines(diff_file.file_path)
        if not file_lines:
            # Fallback to just what's in the hunks if file read fails
            return self._fallback_context(diff_file)

        window = self.settings.CONTEXT_WINDOW_LINES
        changed_lines_set = set(diff_file.added_lines)
        
        # We need to find contiguous blocks of changed lines
        # and expand them by 'window' lines up and down
        if not changed_lines_set:
            return {"file_path": diff_file.file_path, "status": "unchanged", "snippets": []}

        sorted_changes = sorted(list(changed_lines_set))
        blocks = []
        current_block = [sorted_changes[0]]

        for line_no in sorted_changes[1:]:
            if line_no <= current_block[-1] + (window * 2) + 1: # Merge if windows overlap
                current_block.append(line_no)
            else:
                blocks.append(current_block)
                current_block = [line_no]
        blocks.append(current_block)

        snippets = []
        for block in blocks:
            start_line = max(1, block[0] - window)
            end_line = min(len(file_lines), block[-1] + window)
            
            snippet_lines = []
            for i in range(start_line, end_line + 1):
                # i is 1-indexed
                prefix = "+ " if i in changed_lines_set else "  "
                snippet_lines.append(f"{i:4d} | {prefix}{file_lines[i-1]}")
                
            snippets.append({
                "start_line": start_line,
                "end_line": end_line,
                "code": "\n".join(snippet_lines)
            })

        return {
            "file_path": diff_file.file_path,
            "status": "modified" if not diff_file.is_new else "new",
            "snippets": snippets,
            "changed_lines": diff_file.added_lines
        }

    def _fallback_context(self, diff_file: DiffFile) -> Dict[str, Any]:
        """Fallback when actual file cannot be read from disk."""
        snippets = []
        for hunk in diff_file.hunks:
            snippet_lines = []
            for line in hunk.lines:
                prefix = "+ " if line.is_added else "- " if line.is_removed else "  "
                line_no = line.line_number
                snippet_lines.append(f"{line_no:4d} | {prefix}{line.content}")
            snippets.append({
                "start_line": hunk.new_start,
                "end_line": hunk.new_start + hunk.new_lines,
                "code": "\n".join(snippet_lines)
            })
            
        return {
            "file_path": diff_file.file_path,
            "status": "modified" if not diff_file.is_new else "new",
            "snippets": snippets,
            "changed_lines": diff_file.added_lines
        }
