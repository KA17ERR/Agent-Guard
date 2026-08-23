"""
SQLAlchemy engine, session factory, and declarative base.

Supports SQLite (default, for local development) or Postgres (recommended
for deployment — see DEPLOYMENT.md) via a single DATABASE_URL setting.
connect_args/the foreign-key pragma below only apply to SQLite; Postgres
enforces foreign keys and allows multi-threaded connections natively.
"""
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger("agentguard.database")

settings = get_settings()

# Render/Railway/Heroku-style hosted Postgres often hands out a
# DATABASE_URL starting with "postgres://", a legacy scheme SQLAlchemy 2.x
# no longer accepts (it requires "postgresql://"). Normalizing here means
# a platform's auto-injected DATABASE_URL just works without anyone having
# to manually edit it.
_database_url = settings.database_url
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}

engine = create_engine(_database_url, connect_args=connect_args, pool_pre_ping=True)

if _database_url.startswith("sqlite"):
    # SQLite has no real foreign-key enforcement unless this pragma is set
    # per-connection — without it, ondelete="CASCADE" in the models is
    # silently ignored and orphaned rows can accumulate.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session, rolling back any
    uncommitted work if the request raised, and always closing the session
    afterward. Rolling back explicitly (rather than relying on close() to
    do it implicitly) means a failed request never leaves a dangling
    transaction or a half-modified in-memory object graph behind."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def commit_or_rollback(db: Session, *, context: str = "") -> None:
    """Commit the session; on any database error, roll back, log with
    context, and re-raise. Centralizing this means every service gets the
    same rollback-and-log behavior instead of each one reimplementing it
    (or forgetting to)."""
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database commit failed%s", f" while {context}" if context else "")
        raise
