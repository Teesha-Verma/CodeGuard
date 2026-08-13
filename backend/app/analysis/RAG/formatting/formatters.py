"""
Formatting utilities for RAG prompts.
"""
import re
from typing import List


class PromptFormatter:
    """
    Utility class for formatting content into Markdown for prompts.
    """

    @staticmethod
    def format_section(title: str, content: str, level: int = 2) -> str:
        """
        Format a section with a markdown header.
        
        Args:
            title (str): The section title.
            content (str): The content of the section.
            level (int): The header level (default 2).
            
        Returns:
            str: The formatted section.
        """
        prefix = "#" * level
        return f"{prefix} {title}\n\n{content}\n"

    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """
        Format a string as a markdown code block.
        
        Args:
            code (str): The code to format.
            language (str): The programming language for syntax highlighting.
            
        Returns:
            str: The formatted code block.
        """
        return f"```{language}\n{code}\n```\n"

    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]]) -> str:
        """
        Format data as a markdown table.
        
        Args:
            headers (list[str]): Table headers.
            rows (list[list[str]]): Table rows.
            
        Returns:
            str: The formatted markdown table.
        """
        if not headers:
            return ""
            
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "|" + "|".join(["---"] * len(headers)) + "|"
        
        result = [header_row, separator_row]
        for row in rows:
            # Ensure row length matches header length by padding or truncating
            padded_row = row[:len(headers)] + [""] * max(0, len(headers) - len(row))
            result.append("| " + " | ".join(padded_row) + " |")
            
        return "\n".join(result) + "\n"

    @staticmethod
    def format_reference(title: str, file_path: str, line_range: str = "") -> str:
        """
        Format a reference to a file or file section.
        
        Args:
            title (str): Reference title.
            file_path (str): Path to the file.
            line_range (str): Optional line range (e.g., '10-20').
            
        Returns:
            str: The formatted reference.
        """
        ref_text = f"[{title}]({file_path}"
        if line_range:
            ref_text += f"#L{line_range}"
        ref_text += ")"
        return ref_text

    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Clean up markdown text (e.g., collapse multiple newlines).
        
        Args:
            text (str): The markdown text to clean.
            
        Returns:
            str: The cleaned markdown text.
        """
        # Collapse 3 or more consecutive newlines into 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
