"""
Example selection module.
"""
from typing import List
from pydantic import BaseModel


class ExampleItem(BaseModel):
    """
    Data model representing a secure and vulnerable code example.
    """
    title: str
    category: str
    bad_code: str
    good_code: str
    explanation: str
    source: str


class ExampleSelector:
    """
    Selects relevant secure and vulnerable code examples matching detected vulnerabilities.
    """

    def select_examples(
        self,
        vulnerability_types: List[str],
        framework: str = "",
        max_examples: int = 3
    ) -> List[ExampleItem]:
        """
        Selects relevant examples based on vulnerability types and framework.

        Args:
            vulnerability_types: List of vulnerability types (e.g., 'SQL Injection').
            framework: Framework context (e.g., 'Django', 'FastAPI').
            max_examples: Maximum number of examples to return.

        Returns:
            List of selected ExampleItem objects.
        """
        selected_examples: List[ExampleItem] = []
        
        # Logic to fetch and match examples would typically go here.
        # Below is placeholder logic for returning mock examples.
        for vuln in vulnerability_types:
            if len(selected_examples) >= max_examples:
                break
                
            selected_examples.append(
                ExampleItem(
                    title=f"Example for {vuln}",
                    category=vuln,
                    bad_code="# Vulnerable code snippet here",
                    good_code="# Secure code snippet here",
                    explanation=f"Explanation of {vuln} vulnerability and mitigation in {framework if framework else 'general'} context.",
                    source="Internal Database"
                )
            )
            
        return selected_examples[:max_examples]
