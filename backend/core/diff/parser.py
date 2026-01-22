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

        old_lines= None
        new_lines=None

        for line in diff_text.splitlines:

            # new file block

            if line.startswith("diff --git"):
                if current_file:
                    result.append({
                        "file":current_file,
                        "added_lines":added_lines,
                        "removed_lines":removed_lines
                    })
                
                current_file=line.split("b/")[-1]





        