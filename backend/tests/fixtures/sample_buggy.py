# Sample buggy Python file used as a test fixture for static analysis

def append_to_list(value, target=[]):
    """Mutable default argument — classic Python footgun."""
    target.append(value)
    return target

def remove_while_iterating(items):
    """Mutates the list being iterated over."""
    for item in items:
        if item < 0:
            items.remove(item)
    return items

def unsafe_eval(user_input):
    """Uses eval on untrusted input."""
    return eval(user_input)

def bare_except_handler(x):
    """Catches all exceptions including SystemExit."""
    try:
        return 1 / x
    except:
        return 0

def deeply_nested(a, b, c, d):
    """High cyclomatic complexity function."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    return a + b + c + d
                else:
                    return a + b + c
            else:
                if d > 0:
                    return a + b + d
                else:
                    return a + b
        else:
            return a
    else:
        return 0
