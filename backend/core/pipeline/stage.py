from enum import Enum

class Stage (Enum):
    CLONE="clone"
    DIFF = "diff"
    AST = "ast"
    RULES = "rules"
    LLM = "llm"
    ASSEMBLY = "assembly"