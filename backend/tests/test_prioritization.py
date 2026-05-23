from app.static_analysis.prioritization import PrioritizationEngine

def test_prioritization_style_formatting():
    res = PrioritizationEngine.analyze("flake8", "E501", "line too long (82 > 79 characters)")
    assert res["signal_priority"] == "low"
    assert res["issue_category"] == "style-only violations"
    assert res["is_low_signal"] is True

    res2 = PrioritizationEngine.analyze("pylint", "C0116", "Missing function docstring")
    assert res2["signal_priority"] == "low"
    assert res2["is_low_signal"] is True

def test_prioritization_security():
    res = PrioritizationEngine.analyze("bandit", "B307", "Use of unsafe eval() detected")
    assert res["signal_priority"] == "high"
    assert res["issue_category"] == "security"
    assert res["is_low_signal"] is False

def test_prioritization_mutation_loops():
    res = PrioritizationEngine.analyze("ast", "MUTATION_DURING_ITERATION", "Modifying items during loop traversal")
    assert res["signal_priority"] == "high"
    assert res["issue_category"] == "mutation risks"
    assert res["is_low_signal"] is False

def test_prioritization_globals_and_shadowing():
    # Global reassignment
    res = PrioritizationEngine.analyze("ast", "global_modification", "global cache modified")
    assert res["signal_priority"] == "medium"
    assert res["issue_category"] == "runtime logic risks"

    # Shadowing is low-signal style
    res2 = PrioritizationEngine.analyze("ast", "variable_shadowing", "Local variable x shadows global")
    assert res2["signal_priority"] == "low"
    assert res2["issue_category"] == "style-only violations"
    assert res2["is_low_signal"] is True

def test_prioritization_test_file_override():
    # If in test file, a logic risk becomes low priority / style violation
    meta = {
        "is_test_file": True,
        "is_config_file": False,
        "is_migration_file": False,
        "is_generated_file": False
    }
    res = PrioritizationEngine.analyze("ast", "global_modification", "global cache modified", context_meta=meta)
    assert res["signal_priority"] == "low"
    assert res["issue_category"] == "style-only violations"
