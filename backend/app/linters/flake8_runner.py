import subprocess
from typing import List
from app.linters.base import BaseLinter, LinterFinding
from app.core.constants import Severity

class Flake8Runner(BaseLinter):
    def run(self, file_path: str) -> List[LinterFinding]:
        try:
            result = subprocess.run(
                ["flake8", file_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            findings = []
            for line in result.stdout.splitlines():
                # flake8 standard format: path/to/file.py:line:col: rule message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    try:
                        line_no = int(parts[1])
                        msg_part = parts[3].strip()
                        
                        # msg_part is usually something like "E501 line too long"
                        rule_id_parts = msg_part.split(" ", 1)
                        rule_id = rule_id_parts[0] if rule_id_parts else ""
                        message = rule_id_parts[1] if len(rule_id_parts) > 1 else ""
                        
                        findings.append(LinterFinding(
                            line=line_no,
                            rule_id=rule_id,
                            message=message,
                            severity=Severity.MEDIUM, # Flake8 doesn't specify severity natively in this format
                            tool_name="flake8"
                        ))
                    except ValueError:
                        pass
            return findings
        except Exception:
            return []
