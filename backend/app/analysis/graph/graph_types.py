from enum import Enum

class NodeKind(str, Enum):
    GENERIC = "generic"
    CFG_ENTRY = "cfg_entry"
    CFG_EXIT = "cfg_exit"
    CFG_STATEMENT = "cfg_statement"
    CFG_BRANCH = "cfg_branch"
    CFG_JOIN = "cfg_join"
    CALL_FUNCTION = "call_function"
    CALL_METHOD = "call_method"

class EdgeKind(str, Enum):
    GENERIC = "generic"
    CFG_NORMAL = "cfg_normal"
    CFG_TRUE = "cfg_true"
    CFG_FALSE = "cfg_false"
    CALL = "call"
