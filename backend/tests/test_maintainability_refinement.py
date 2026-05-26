import pytest
from app.static_analysis.complexity_analyzer import ComplexityAnalyzer
from app.core.config import get_settings

def test_maintainability_interpretation_declarative_schema():
    # Setup settings to trigger MI threshold breach (Radon base MI is around 100 for empty, lower for complex)
    # We will write a code block that has low maintainability index
    complex_schema_code = """
class UserSchema:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        if self.a:
            if self.b:
                if self.c:
                    print(1)
        else:
            print(2)
"""
    analyzer = ComplexityAnalyzer()
    
    # Temporarily set high minimum maintainability threshold to guarantee breach
    settings = get_settings()
    old_mi_min = settings.MAINTAINABILITY_INDEX_MIN
    settings.MAINTAINABILITY_INDEX_MIN = 101  # Guarantee breach since maximum MI is 100
    
    try:
        # Test as declarative schema file
        res_decl = analyzer.analyze(complex_schema_code, "app/schemas/user_schema.py")
        assert res_decl["mi_exceeds_threshold"] is True
        assert "mi_interpretation" in res_decl
        assert "structural abstractions or configurations" in res_decl["mi_interpretation"]
        assert "No critical refactoring is recommended" in res_decl["mi_interpretation"]
        assert "cognitive density" not in res_decl["mi_interpretation"]
        assert "lower maintainability" not in res_decl["mi_interpretation"]
    finally:
        settings.MAINTAINABILITY_INDEX_MIN = old_mi_min


def test_maintainability_interpretation_business_logic():
    complex_business_code = """
def process_invoice(invoice):
    if invoice.status == 'pending':
        if invoice.amount > 1000:
            if invoice.user.is_verified:
                invoice.approve()
            else:
                invoice.flag()
        else:
            invoice.approve()
    elif invoice.status == 'failed':
        invoice.retry()
    else:
        invoice.cancel()
"""
    analyzer = ComplexityAnalyzer()
    
    settings = get_settings()
    old_mi_min = settings.MAINTAINABILITY_INDEX_MIN
    settings.MAINTAINABILITY_INDEX_MIN = 101  # Guarantee breach since maximum MI is 100
    
    try:
        # Test as regular service business logic file
        res_logic = analyzer.analyze(complex_business_code, "app/services/payment_service.py")
        assert res_logic["mi_exceeds_threshold"] is True
        assert "mi_interpretation" in res_logic
        assert "business logic in this file has higher structural complexity" in res_logic["mi_interpretation"]
        assert "Consider simplifying conditional branches" in res_logic["mi_interpretation"]
        assert "cognitive density" not in res_logic["mi_interpretation"]
        assert "lower maintainability" not in res_logic["mi_interpretation"]
    finally:
        settings.MAINTAINABILITY_INDEX_MIN = old_mi_min


def test_function_complexity_nuanced_wording():
    # Write a highly complex function to trigger CC exceeds breach
    code = """
def nested_if_branches(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return 1
    return 0
"""
    analyzer = ComplexityAnalyzer()
    
    settings = get_settings()
    old_cc_max = settings.CYCLOMATIC_COMPLEXITY_MAX
    settings.CYCLOMATIC_COMPLEXITY_MAX = 2  # Guarantee breach
    
    try:
        res = analyzer.analyze(code, "app/utils.py")
        assert len(res["functions"]) == 1
        func = res["functions"][0]
        assert func["exceeds_threshold"] is True
        assert "interpretation" in func
        assert "higher number of execution paths" in func["interpretation"]
        assert "Simplifying the control flow" in func["interpretation"]
        assert "difficult to cover with unit tests" not in func["interpretation"]
    finally:
        settings.CYCLOMATIC_COMPLEXITY_MAX = old_cc_max
