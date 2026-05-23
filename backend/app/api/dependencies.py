from typing import Generator
from fastapi import Request
from app.core.config import Settings, get_settings
from app.core.logger import get_logger
import logging

def get_app_settings() -> Settings:
    """Dependency for getting app settings."""
    return get_settings()

def get_app_logger() -> logging.Logger:
    """Dependency for getting the app logger."""
    return get_logger("codeguard.api")

# Database session dependency will be added in Phase 8
