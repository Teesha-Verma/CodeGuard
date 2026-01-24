 # parsing : converting raw git diff into structured change facts.
import re 
from typing import List, Dict

class diffParser:
    HUNK_PATTERN=re.compile(r"@@ -(\d+),?\d* \+(\d+),?\d* @@")
    def parse(self, diff_text:str)-> List[Dict]:

        result=[]

        current_file=None
        added_lines=[]
        removed_lines=[]

        old_line_no= None
        new_line_no=None

        for line in diff_text.splitlines():

            # new file block

            if line.startswith("diff --git"):
                if current_file:
                    result.append({
                        "file":current_file,
                        "added_lines":added_lines,
                        "removed_lines":removed_lines
                    })
                
                current_file=line.split("b/")[-1]
                added_lines = []
                removed_lines = []
                old_line_no = None
                new_line_no = None

            # Hunk header
            elif line.startswith("@@"):
                match = self.HUNK_PATTERN.search(line)
                if match:
                    old_line_no = int(match.group(1))
                    new_line_no = int(match.group(2))

            # Removed line
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines.append(old_line_no)
                old_line_no += 1

            # Added line
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines.append(new_line_no)
                new_line_no += 1

            # Context line
            else:
                if old_line_no is not None:
                    old_line_no += 1
                if new_line_no is not None:
                    new_line_no += 1

        # Flush last file
        if current_file:
            result.append({
                "file": current_file,
                "added_lines": added_lines,
                "removed_lines": removed_lines
            })

        return result
                





        