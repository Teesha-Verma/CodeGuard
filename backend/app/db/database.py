from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily create and cache the SQLAlchemy engine with configurable pooling."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
    return _engine


def _get_session_factory():
    """Lazily create and cache the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_get_engine()
        )
    return _SessionLocal


def _reset_engine_cache():
    """Reset cached engine and session factory (useful for testing)."""
    global _engine, _SessionLocal
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _SessionLocal = None


# Public accessors — maintain backward compatibility
engine = property(lambda self: _get_engine())


class _EngineProxy:
    """Proxy that defers engine creation until first attribute access."""
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

    def __repr__(self):
        settings = get_settings()
        return f"<Engine({settings.get_masked_database_url()})>"


engine = _EngineProxy()


class _SessionLocalProxy:
    """Proxy that defers SessionLocal creation until first call."""
    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(_get_session_factory(), name)


SessionLocal = _SessionLocalProxy()


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()
