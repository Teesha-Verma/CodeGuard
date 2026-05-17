import subprocess
import json
from typing import List
from app.linters.base import BaseLinter, LinterFinding
from app.core.constants import Severity

class BanditRunner(BaseLinter):
    """Security linter for Python."""
    
    def __init__(self):
        self.severity_map = {
            "HIGH": Severity.CRITICAL,
            "MEDIUM": Severity.HIGH,
            "LOW": Severity.MEDIUM
        }

    def run(self, file_path: str) -> List[LinterFinding]:
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", file_path],
                capture_output=True,
                text=True,
                check=False
            )
            if not result.stdout:
                return []
                
            data = json.loads(result.stdout)
            findings = []
            for item in data.get("results", []):
                findings.append(LinterFinding(
                    line=item.get("line_number", 1),
                    rule_id=item.get("test_id", ""),
                    message=item.get("issue_text", ""),
                    severity=self.severity_map.get(item.get("issue_severity", "LOW"), Severity.MEDIUM),
                    tool_name="bandit"
                ))
            return findings
        except Exception:
            return []
