from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from regret.config import Settings, get_settings
from regret.db.base import Base
from regret.security import ensure_data_dir

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _sqlite_connect(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    settings = settings or get_settings()
    if _engine is not None:
        return _engine
    ensure_data_dir(settings)
    connect_args = {}
    if settings.regret_database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    _engine = create_engine(
        settings.regret_database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    if settings.regret_database_url.startswith("sqlite"):
        event.listen(_engine, "connect", _sqlite_connect)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(settings), autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def init_db(settings: Settings | None = None) -> None:
    """Create tables. Production should also run Alembic migrations."""
    import regret.models  # noqa: F401

    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)
    _ensure_oauth_scopes_column(engine)


def _ensure_oauth_scopes_column(engine: Engine) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "oauth_states" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("oauth_states")}
    if "scopes" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE oauth_states ADD COLUMN scopes VARCHAR(255) DEFAULT 'data'"))


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def healthcheck_db(settings: Settings | None = None) -> bool:
    engine = get_engine(settings)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
