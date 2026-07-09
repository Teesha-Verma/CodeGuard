"""
Repository Intelligence Layer — Constants.

Stores architecture names, layer names, risk thresholds,
complexity thresholds, hotspot thresholds, dependency thresholds,
and classification constants.
"""

from enum import Enum
from typing import Dict, List, FrozenSet


# ═══════════════════════════════════════════════════════════════════
# Architecture Names
# ═══════════════════════════════════════════════════════════════════

class Architecture(str, Enum):
    """Known software architecture patterns."""
    MVC = "mvc"
    CLEAN = "clean_architecture"
    HEXAGONAL = "hexagonal"
    LAYERED = "layered"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    PACKAGE_BY_FEATURE = "package_by_feature"
    REPOSITORY_PATTERN = "repository_pattern"
    SERVICE_LAYER = "service_layer"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════
# Layer Names
# ═══════════════════════════════════════════════════════════════════

class Layer(str, Enum):
    """Logical layers in a software architecture."""
    CONTROLLER = "controller"
    SERVICE = "service"
    MODEL = "model"
    REPOSITORY = "repository"
    INFRASTRUCTURE = "infrastructure"
    DOMAIN = "domain"
    API = "api"
    UTILITY = "utility"
    TEST = "test"
    CONFIGURATION = "configuration"
    MIDDLEWARE = "middleware"
    SCHEMA = "schema"
    DTO = "dto"
    MIGRATION = "migration"
    SECURITY = "security"
    DATABASE = "database"
    CLI = "cli"
    TEMPLATE = "template"
    GENERATED = "generated"
    DECORATOR = "decorator"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════
# File Classification Categories
# ═══════════════════════════════════════════════════════════════════

class FileCategory(str, Enum):
    """Categories for semantic file tagging."""
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    MODEL = "model"
    SCHEMA = "schema"
    DTO = "dto"
    UTILITY = "utility"
    CONFIGURATION = "configuration"
    MIGRATION = "migration"
    GENERATED = "generated"
    TEST = "test"
    CLI = "cli"
    API = "api"
    MIDDLEWARE = "middleware"
    DECORATOR = "decorator"
    SECURITY = "security"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    TEMPLATE = "template"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════
# Severity Levels
# ═══════════════════════════════════════════════════════════════════

class Severity(str, Enum):
    """Severity levels for violations and findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ═══════════════════════════════════════════════════════════════════
# Repository Graph Node/Edge Kinds
# ═══════════════════════════════════════════════════════════════════

class RepoNodeKind(str, Enum):
    """Node kinds in the Repository Graph."""
    FILE = "repo_file"
    PACKAGE = "repo_package"
    MODULE = "repo_module"
    LAYER = "repo_layer"
    ARCHITECTURE = "repo_architecture"


class RepoEdgeKind(str, Enum):
    """Edge kinds in the Repository Graph."""
    IMPORTS = "repo_imports"
    CONTAINS = "repo_contains"
    DEPENDS_ON = "repo_depends_on"
    BELONGS_TO_LAYER = "repo_belongs_to_layer"
    BELONGS_TO_PACKAGE = "repo_belongs_to_package"


# ═══════════════════════════════════════════════════════════════════
# Thresholds
# ═══════════════════════════════════════════════════════════════════

# Risk thresholds
RISK_THRESHOLD_CRITICAL: float = 0.85
RISK_THRESHOLD_HIGH: float = 0.65
RISK_THRESHOLD_MEDIUM: float = 0.40
RISK_THRESHOLD_LOW: float = 0.20

# Complexity thresholds
COMPLEXITY_THRESHOLD_HIGH: int = 20
COMPLEXITY_THRESHOLD_MEDIUM: int = 10
COMPLEXITY_THRESHOLD_LOW: int = 5

# Hotspot thresholds
HOTSPOT_MIN_IMPORTS: int = 10
HOTSPOT_MIN_CALLERS: int = 8
HOTSPOT_MIN_FAN_IN: int = 10
HOTSPOT_MIN_FAN_OUT: int = 15
HOTSPOT_MIN_LINES: int = 500
HOTSPOT_TOP_N: int = 20

# Dependency thresholds
DEPENDENCY_HEAVY_CHAIN_LENGTH: int = 5
DEPENDENCY_MAX_FAN_OUT: int = 20
DEPENDENCY_MAX_FAN_IN: int = 30

# File size thresholds (lines)
FILE_SIZE_LARGE: int = 500
FILE_SIZE_VERY_LARGE: int = 1000

# Confidence thresholds
CONFIDENCE_HIGH: float = 0.80
CONFIDENCE_MEDIUM: float = 0.50
CONFIDENCE_LOW: float = 0.25


# ═══════════════════════════════════════════════════════════════════
# Classification Patterns
# ═══════════════════════════════════════════════════════════════════

# File name patterns → FileCategory
FILE_NAME_PATTERNS: Dict[str, FileCategory] = {
    "controller": FileCategory.CONTROLLER,
    "view": FileCategory.CONTROLLER,
    "views": FileCategory.CONTROLLER,
    "handler": FileCategory.CONTROLLER,
    "endpoint": FileCategory.CONTROLLER,
    "route": FileCategory.API,
    "routes": FileCategory.API,
    "router": FileCategory.API,
    "api": FileCategory.API,
    "service": FileCategory.SERVICE,
    "services": FileCategory.SERVICE,
    "usecase": FileCategory.SERVICE,
    "use_case": FileCategory.SERVICE,
    "interactor": FileCategory.SERVICE,
    "model": FileCategory.MODEL,
    "models": FileCategory.MODEL,
    "entity": FileCategory.MODEL,
    "entities": FileCategory.MODEL,
    "schema": FileCategory.SCHEMA,
    "schemas": FileCategory.SCHEMA,
    "serializer": FileCategory.SCHEMA,
    "serializers": FileCategory.SCHEMA,
    "dto": FileCategory.DTO,
    "repository": FileCategory.REPOSITORY,
    "repositories": FileCategory.REPOSITORY,
    "repo": FileCategory.REPOSITORY,
    "dao": FileCategory.REPOSITORY,
    "util": FileCategory.UTILITY,
    "utils": FileCategory.UTILITY,
    "utility": FileCategory.UTILITY,
    "utilities": FileCategory.UTILITY,
    "helper": FileCategory.UTILITY,
    "helpers": FileCategory.UTILITY,
    "common": FileCategory.UTILITY,
    "config": FileCategory.CONFIGURATION,
    "configuration": FileCategory.CONFIGURATION,
    "settings": FileCategory.CONFIGURATION,
    "conf": FileCategory.CONFIGURATION,
    "migration": FileCategory.MIGRATION,
    "migrations": FileCategory.MIGRATION,
    "alembic": FileCategory.MIGRATION,
    "test": FileCategory.TEST,
    "tests": FileCategory.TEST,
    "test_": FileCategory.TEST,
    "conftest": FileCategory.TEST,
    "fixture": FileCategory.TEST,
    "fixtures": FileCategory.TEST,
    "cli": FileCategory.CLI,
    "command": FileCategory.CLI,
    "commands": FileCategory.CLI,
    "manage": FileCategory.CLI,
    "middleware": FileCategory.MIDDLEWARE,
    "middlewares": FileCategory.MIDDLEWARE,
    "decorator": FileCategory.DECORATOR,
    "decorators": FileCategory.DECORATOR,
    "security": FileCategory.SECURITY,
    "auth": FileCategory.SECURITY,
    "authentication": FileCategory.SECURITY,
    "authorization": FileCategory.SECURITY,
    "permission": FileCategory.SECURITY,
    "permissions": FileCategory.SECURITY,
    "database": FileCategory.DATABASE,
    "db": FileCategory.DATABASE,
    "infra": FileCategory.INFRASTRUCTURE,
    "infrastructure": FileCategory.INFRASTRUCTURE,
    "template": FileCategory.TEMPLATE,
    "templates": FileCategory.TEMPLATE,
    "generated": FileCategory.GENERATED,
    "auto_generated": FileCategory.GENERATED,
    "pb2": FileCategory.GENERATED,
}

# Directory patterns → FileCategory
DIRECTORY_PATTERNS: Dict[str, FileCategory] = {
    "controllers": FileCategory.CONTROLLER,
    "views": FileCategory.CONTROLLER,
    "handlers": FileCategory.CONTROLLER,
    "api": FileCategory.API,
    "routes": FileCategory.API,
    "endpoints": FileCategory.API,
    "services": FileCategory.SERVICE,
    "usecases": FileCategory.SERVICE,
    "models": FileCategory.MODEL,
    "entities": FileCategory.MODEL,
    "domain": FileCategory.MODEL,
    "schemas": FileCategory.SCHEMA,
    "serializers": FileCategory.SCHEMA,
    "dtos": FileCategory.DTO,
    "repositories": FileCategory.REPOSITORY,
    "repos": FileCategory.REPOSITORY,
    "dao": FileCategory.REPOSITORY,
    "utils": FileCategory.UTILITY,
    "helpers": FileCategory.UTILITY,
    "common": FileCategory.UTILITY,
    "lib": FileCategory.UTILITY,
    "config": FileCategory.CONFIGURATION,
    "settings": FileCategory.CONFIGURATION,
    "conf": FileCategory.CONFIGURATION,
    "migrations": FileCategory.MIGRATION,
    "alembic": FileCategory.MIGRATION,
    "tests": FileCategory.TEST,
    "test": FileCategory.TEST,
    "spec": FileCategory.TEST,
    "cli": FileCategory.CLI,
    "commands": FileCategory.CLI,
    "management": FileCategory.CLI,
    "middleware": FileCategory.MIDDLEWARE,
    "middlewares": FileCategory.MIDDLEWARE,
    "decorators": FileCategory.DECORATOR,
    "security": FileCategory.SECURITY,
    "auth": FileCategory.SECURITY,
    "database": FileCategory.DATABASE,
    "db": FileCategory.DATABASE,
    "infra": FileCategory.INFRASTRUCTURE,
    "infrastructure": FileCategory.INFRASTRUCTURE,
    "templates": FileCategory.TEMPLATE,
    "generated": FileCategory.GENERATED,
}


# ═══════════════════════════════════════════════════════════════════
# Architecture Detection Signals
# ═══════════════════════════════════════════════════════════════════

# Directories that signal an architecture
ARCHITECTURE_SIGNALS: Dict[Architecture, List[str]] = {
    Architecture.MVC: ["controllers", "models", "views", "templates"],
    Architecture.CLEAN: ["domain", "usecases", "entities", "interfaces", "adapters"],
    Architecture.HEXAGONAL: ["ports", "adapters", "domain", "application"],
    Architecture.LAYERED: ["presentation", "business", "data", "persistence"],
    Architecture.MICROSERVICE: ["gateway", "discovery", "config-server"],
    Architecture.REPOSITORY_PATTERN: ["repositories", "repos", "dao"],
    Architecture.SERVICE_LAYER: ["services", "service"],
    Architecture.PACKAGE_BY_FEATURE: [],  # Detected by structure analysis
}

# Layer dependency rules: layer → set of layers it should NOT import from
LAYER_RULES: Dict[Layer, FrozenSet[Layer]] = {
    Layer.CONTROLLER: frozenset({Layer.INFRASTRUCTURE, Layer.DATABASE, Layer.MIGRATION}),
    Layer.MODEL: frozenset({Layer.API, Layer.CONTROLLER, Layer.SERVICE, Layer.INFRASTRUCTURE}),
    Layer.SERVICE: frozenset({Layer.CONTROLLER, Layer.API}),
    Layer.DOMAIN: frozenset({Layer.API, Layer.CONTROLLER, Layer.INFRASTRUCTURE, Layer.DATABASE}),
    Layer.REPOSITORY: frozenset({Layer.CONTROLLER, Layer.API}),
    Layer.UTILITY: frozenset({Layer.CONTROLLER, Layer.SERVICE, Layer.API}),
    Layer.INFRASTRUCTURE: frozenset({Layer.CONTROLLER, Layer.API}),
    Layer.TEST: frozenset(),  # Tests can import anything
    Layer.SCHEMA: frozenset({Layer.CONTROLLER, Layer.API, Layer.INFRASTRUCTURE}),
}

# Frameworks detected by import patterns
FRAMEWORK_INDICATORS: Dict[str, str] = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "aiohttp": "aiohttp",
    "pyramid": "Pyramid",
    "bottle": "Bottle",
    "sanic": "Sanic",
    "falcon": "Falcon",
    "celery": "Celery",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "pytest": "pytest",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "scipy": "SciPy",
    "sklearn": "scikit-learn",
}
