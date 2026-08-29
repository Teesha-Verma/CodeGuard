import subprocess
import json
import logging
from typing import List, Optional
from app.linters.base import BaseLinter, LinterFinding
from app.core.constants import Severity
from app.core.config import get_settings

logger = logging.getLogger("codeguard.linters.bandit")


class BanditRunner(BaseLinter):
    """Security linter for Python."""

    def __init__(self, timeout: Optional[int] = None):
        settings = get_settings()
        self.timeout = timeout if timeout is not None else getattr(settings, "LINTER_TIMEOUT", 15)
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
                check=False,
                timeout=self.timeout
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
        except subprocess.TimeoutExpired:
            logger.warning(f"Bandit timed out after {self.timeout}s for {file_path}")
            return []
        except Exception as e:
            logger.debug(f"Bandit execution error for {file_path}: {e}")
            return []
