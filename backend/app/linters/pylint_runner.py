import subprocess
import json
import logging
from typing import List, Optional
from app.linters.base import BaseLinter, LinterFinding
from app.core.constants import Severity
from app.core.config import get_settings

logger = logging.getLogger("codeguard.linters.pylint")


class PylintRunner(BaseLinter):
    def __init__(self, timeout: Optional[int] = None):
        settings = get_settings()
        self.timeout = timeout if timeout is not None else getattr(settings, "LINTER_TIMEOUT", 15)
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
                check=False,
                timeout=self.timeout
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
        except subprocess.TimeoutExpired:
            logger.warning(f"Pylint timed out after {self.timeout}s for {file_path}")
            return []
        except Exception as e:
            logger.debug(f"Pylint execution error for {file_path}: {e}")
            return []
