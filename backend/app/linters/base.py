from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from app.core.constants import Severity

@dataclass
class LinterFinding:
    line: int
    rule_id: str
    message: str
    severity: Severity
    tool_name: str

class BaseLinter(ABC):
    @abstractmethod
    def run(self, file_path: str) -> List[LinterFinding]:
        """Runs the linter on the specified file and returns structured findings."""
        pass
