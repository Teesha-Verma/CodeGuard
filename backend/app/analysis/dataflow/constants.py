"""
Data Flow Analysis — Constants and Enums.

Extends the shared Graph Foundation's NodeKind/EdgeKind with
data-flow-specific categories.
"""

from enum import Enum


# ── Data Flow Node Kinds ─────────────────────────────────────────

class DataFlowNodeKind(str, Enum):
    """Kinds of nodes in the Data Flow Graph."""
    VARIABLE = "df_variable"
    PARAMETER = "df_parameter"
    LITERAL = "df_literal"
    CONSTANT = "df_constant"
    RETURN_VALUE = "df_return_value"
    ATTRIBUTE = "df_attribute"
    FUNCTION_ARG = "df_function_arg"
    COLLECTION_ELEMENT = "df_collection_element"
    CALL_RESULT = "df_call_result"
    IMPORT = "df_import"


# ── Data Flow Edge Kinds ─────────────────────────────────────────

class DataFlowEdgeKind(str, Enum):
    """Kinds of edges in the Data Flow Graph."""
    ASSIGNMENT = "df_assignment"
    PARAMETER_PASS = "df_parameter_pass"
    RETURN_PROPAGATION = "df_return_propagation"
    ALIAS = "df_alias"
    ATTRIBUTE_WRITE = "df_attribute_write"
    COLLECTION_WRITE = "df_collection_write"
    FUNCTION_CALL = "df_function_call"
    AUGMENTED_ASSIGN = "df_augmented_assign"
    TUPLE_UNPACK = "df_tuple_unpack"


# ── Taint Categories ─────────────────────────────────────────────

class TaintKind(str, Enum):
    """Categories of taint labels."""
    USER_INPUT = "user_input"
    HTTP_PARAMETER = "http_parameter"
    ENVIRONMENT = "environment"
    CLI_ARGUMENT = "cli_argument"
    FILE_READ = "file_read"
    NETWORK_INPUT = "network_input"
    DESERIALIZED = "deserialized"
    UNTRUSTED = "untrusted"


# ── Vulnerability Severity ───────────────────────────────────────

class Severity(str, Enum):
    """Severity levels for vulnerability findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
