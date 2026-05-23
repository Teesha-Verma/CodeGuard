import subprocess
import json
from typing import List
from app.linters.base import BaseLinter, LinterFinding
from app.core.constants import Severity

class PylintRunner(BaseLinter):
    def __init__(self):
        self.severity_map = {
            "fatal": Severity.CRITICAL,
            "error": Severity.HIGH,
            "warning": Severity.MEDIUM,
            "refactor": Severity.LOW,
            "convention": Severity.INFO
        }

    def run(self, file_path: str) -> List[LinterFinding]:
        try:
            result = subprocess.run(
                ["pylint", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            if not result.stdout:
                return []
                
            data = json.loads(result.stdout)
            findings = []
            for item in data:
                findings.append(LinterFinding(
                    line=item.get("line", 1),
                    rule_id=item.get("message-id", ""),
                    message=item.get("message", ""),
                    severity=self.severity_map.get(item.get("type", "warning"), Severity.MEDIUM),
                    tool_name="pylint"
                ))
            return findings
        except Exception:
            # Fallback if pylint fails to run or output invalid JSON
            return []
