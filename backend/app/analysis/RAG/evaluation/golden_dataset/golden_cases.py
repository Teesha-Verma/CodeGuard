"""
Golden dataset management for RAG Evaluation.
"""

from typing import Any, List
from pydantic import BaseModel, Field


class GoldenTestCase(BaseModel):
    """
    Represents a golden test case for evaluating the RAG pipeline.
    """
    case_id: str = Field(..., description="Unique identifier for the test case")
    language: str = Field(..., description="Programming language of the code sample")
    framework: str = Field(..., description="Framework used in the code sample")
    category: str = Field(..., description="Vulnerability or issue category")
    code_sample: str = Field(..., description="The source code to be analyzed")
    ground_truth_findings: List[dict[str, Any]] = Field(..., description="Expected findings")
    ground_truth_severity: str = Field(..., description="Expected severity level")
    ground_truth_confidence: float = Field(..., description="Expected confidence score")
    expected_references: List[str] = Field(default_factory=list, description="Expected reference URLs or docs")
    expected_knowledge_sources: List[str] = Field(default_factory=list, description="Expected knowledge sources")


class GoldenDatasetManager:
    """
    Manager for the golden dataset.
    """

    def __init__(self) -> None:
        """Initialize the GoldenDatasetManager with a predefined set of cases."""
        self._dataset: List[GoldenTestCase] = self._load_default_dataset()

    def _load_default_dataset(self) -> List[GoldenTestCase]:
        """
        Loads the pre-populated golden test cases.
        
        Returns:
            List[GoldenTestCase]: A list of predefined golden test cases.
        """
        return [
            GoldenTestCase(
                case_id="SQLI-001",
                language="Python",
                framework="Flask",
                category="SQL Injection",
                code_sample="query = f'SELECT * FROM users WHERE username = {username}'\ncursor.execute(query)",
                ground_truth_findings=[{"type": "sql_injection", "line": 2}],
                ground_truth_severity="High",
                ground_truth_confidence=0.95,
                expected_references=["CWE-89"],
                expected_knowledge_sources=["owasp_top_10"]
            ),
            GoldenTestCase(
                case_id="XSS-001",
                language="JavaScript",
                framework="React",
                category="XSS",
                code_sample="<div dangerouslySetInnerHTML={{__html: userInput}} />",
                ground_truth_findings=[{"type": "cross_site_scripting", "line": 1}],
                ground_truth_severity="High",
                ground_truth_confidence=0.9,
                expected_references=["CWE-79"],
                expected_knowledge_sources=["owasp_top_10"]
            ),
            GoldenTestCase(
                case_id="NPLUS1-001",
                language="Python",
                framework="Django",
                category="N+1 Query",
                code_sample="for user in User.objects.all():\n    print(user.profile.bio)",
                ground_truth_findings=[{"type": "n_plus_one_query", "line": 2}],
                ground_truth_severity="Medium",
                ground_truth_confidence=0.85,
                expected_references=["Django Performance"],
                expected_knowledge_sources=["django_docs"]
            ),
            GoldenTestCase(
                case_id="ASYNC-001",
                language="Python",
                framework="FastAPI",
                category="Async IO blocking",
                code_sample="import time\n\n@app.get('/')\nasync def read_root():\n    time.sleep(5)\n    return {'Hello': 'World'}",
                ground_truth_findings=[{"type": "blocking_call_in_async", "line": 5}],
                ground_truth_severity="Medium",
                ground_truth_confidence=0.90,
                expected_references=["FastAPI Async Guide"],
                expected_knowledge_sources=["fastapi_docs"]
            ),
            GoldenTestCase(
                case_id="DESER-001",
                language="Python",
                framework="Standard Library",
                category="Insecure Deserialization",
                code_sample="import pickle\npickle.loads(user_input)",
                ground_truth_findings=[{"type": "insecure_deserialization", "line": 2}],
                ground_truth_severity="Critical",
                ground_truth_confidence=0.99,
                expected_references=["CWE-502"],
                expected_knowledge_sources=["owasp_top_10"]
            ),
            GoldenTestCase(
                case_id="SECRETS-001",
                language="Python",
                framework="Any",
                category="Hardcoded Secrets",
                code_sample="AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'",
                ground_truth_findings=[{"type": "hardcoded_secret", "line": 1}],
                ground_truth_severity="High",
                ground_truth_confidence=0.98,
                expected_references=["CWE-798"],
                expected_knowledge_sources=["owasp_top_10"]
            ),
            GoldenTestCase(
                case_id="DB-001",
                language="SQL",
                framework="Any",
                category="Missing Index",
                code_sample="SELECT * FROM large_table WHERE non_indexed_column = 'value';",
                ground_truth_findings=[{"type": "missing_index", "line": 1}],
                ground_truth_severity="Low",
                ground_truth_confidence=0.8,
                expected_references=["Database Performance Tuning"],
                expected_knowledge_sources=["db_optimization_guide"]
            )
        ]

    def get_golden_dataset(self) -> List[GoldenTestCase]:
        """
        Returns the full golden dataset.
        
        Returns:
            List[GoldenTestCase]: All golden test cases.
        """
        return self._dataset

    def get_cases_by_category(self, category: str) -> List[GoldenTestCase]:
        """
        Retrieves test cases matching a specific category.
        
        Args:
            category (str): The category to filter by.
            
        Returns:
            List[GoldenTestCase]: The filtered test cases.
        """
        cat_lower = category.lower()
        return [
            case for case in self._dataset 
            if cat_lower in case.category.lower() 
            or case.category.lower() in cat_lower
            or (cat_lower == "security" and case.category.lower() in ("sql injection", "xss", "insecure deserialization", "hardcoded secrets"))
        ]
