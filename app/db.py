from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().database_url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(url, echo=False, future=True, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


@contextmanager
def get_session():
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine=None):
    from . import models  # noqa: F401 ensure models are imported

    if engine is None:
        engine = get_engine()

    Base.metadata.create_all(bind=engine)


def setup_trgm():
    """Best-effort: enable pg_trgm and create index for faster ILIKE if using Postgres."""
    engine = get_engine()
    url = str(engine.url)
    if not url.startswith("postgresql+"):
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                # enable extension (no-op if exists)
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
            )
            # create GIN index optimized for trigram searches
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_products_norm_name_trgm
                ON products USING gin (normalized_name gin_trgm_ops);
                """
            )
    except Exception:
        # ignore if DB user cannot create extension/index
        pass


def setup_fts():
    """Create tsvector column and GIN index for full-text search if Postgres."""
    engine = get_engine()
    url = str(engine.url)
    if not url.startswith("postgresql+"):
        return
    try:
        with engine.begin() as conn:
            # add tsvector column if missing
            conn.execute(
                """
                ALTER TABLE products
                ADD COLUMN IF NOT EXISTS normalized_name_tsv tsvector;
                """
            )
            # populate once
            conn.execute(
                """
                UPDATE products
                SET normalized_name_tsv = to_tsvector('simple', normalized_name)
                WHERE normalized_name_tsv IS NULL;
                """
            )
            # index
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_products_norm_name_tsv
                ON products USING gin (normalized_name_tsv);
                """
            )
        
    except Exception:
        pass


