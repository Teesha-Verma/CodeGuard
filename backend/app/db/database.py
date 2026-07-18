from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily create and cache the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
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


# Public accessors — maintain backward compatibility
engine = property(lambda self: _get_engine())


class _EngineProxy:
    """Proxy that defers engine creation until first attribute access."""
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

    def __repr__(self):
        return repr(_get_engine())


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
