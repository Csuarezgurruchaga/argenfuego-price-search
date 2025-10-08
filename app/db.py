from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
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
            conn.execute(text(
                # enable extension (no-op if exists)
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
            ))
            # create GIN index optimized for trigram searches
            conn.execute(text(
                """
                CREATE INDEX IF NOT EXISTS ix_products_norm_name_trgm
                ON products USING gin (normalized_name gin_trgm_ops);
                """
            ))
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
            conn.execute(text(
                """
                ALTER TABLE products
                ADD COLUMN IF NOT EXISTS normalized_name_tsv tsvector;
                """
            ))
            # populate once
            conn.execute(text(
                """
                UPDATE products
                SET normalized_name_tsv = to_tsvector('simple', normalized_name)
                WHERE normalized_name_tsv IS NULL;
                """
            ))
            # index
            conn.execute(text(
                """
                CREATE INDEX IF NOT EXISTS ix_products_norm_name_tsv
                ON products USING gin (normalized_name_tsv);
                """
            ))
        
    except Exception:
        pass


def migrate_settings_table():
    """Add new pricing columns to settings table if they don't exist."""
    engine = get_engine()
    url = str(engine.url)
    if not url.startswith("postgresql+"):
        return
    try:
        with engine.begin() as conn:
            # Add default_iva column
            conn.execute(text(
                """
                ALTER TABLE settings
                ADD COLUMN IF NOT EXISTS default_iva DOUBLE PRECISION NOT NULL DEFAULT 1.21;
                """
            ))
            # Add default_iibb column
            conn.execute(text(
                """
                ALTER TABLE settings
                ADD COLUMN IF NOT EXISTS default_iibb DOUBLE PRECISION NOT NULL DEFAULT 1.025;
                """
            ))
            # Add default_profit column
            conn.execute(text(
                """
                ALTER TABLE settings
                ADD COLUMN IF NOT EXISTS default_profit DOUBLE PRECISION NOT NULL DEFAULT 2.0;
                """
            ))
            print("[DB] Settings table migrated successfully with new pricing columns.")
    except Exception as e:
        print(f"[DB] Could not migrate settings table: {e}")


def migrate_to_product_prices():
    """Migrate existing products to new ProductPrice model."""
    from .models import Product, ProductPrice, Upload
    engine = get_engine()
    url = str(engine.url)
    
    # Make products.unit_price nullable for Postgres
    if url.startswith("postgresql+"):
        try:
            with engine.begin() as conn:
                # Make legacy columns nullable
                conn.execute(text(
                    """
                    ALTER TABLE products 
                    ALTER COLUMN unit_price DROP NOT NULL,
                    ALTER COLUMN currency DROP NOT NULL,
                    ALTER COLUMN source_file_id DROP NOT NULL,
                    ALTER COLUMN last_seen_at DROP NOT NULL;
                    """
                ))
                print("[DB] Made products legacy columns nullable.")
        except Exception as e:
            print(f"[DB] Could not alter products columns: {e}")
    
    # Migrate existing data
    try:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        
        # Check if product_prices table exists and has data
        try:
            existing_prices_count = session.execute(text("SELECT COUNT(*) FROM product_prices")).scalar()
            if existing_prices_count > 0:
                print(f"[DB] ProductPrice table already has {existing_prices_count} records. Skipping migration.")
                session.close()
                return
        except Exception:
            # Table doesn't exist yet, that's fine
            pass
        
        # Find products with prices but no ProductPrice entries
        products = session.query(Product).filter(
            Product.unit_price.isnot(None)
        ).all()
        
        migrated_count = 0
        for product in products:
            # Check if this product already has a price entry
            existing_price = session.query(ProductPrice).filter(
                ProductPrice.product_id == product.id
            ).first()
            
            if existing_price:
                continue  # Already migrated
            
            # Extract provider name from upload filename
            provider_name = "Unknown"
            if product.source_file_id:
                upload = session.query(Upload).filter(Upload.id == product.source_file_id).first()
                if upload and upload.filename:
                    # Extract first filename if multiple were uploaded together
                    fname = upload.filename.split(",")[0].strip()
                    # Remove extension and clean up
                    provider_name = fname.rsplit(".", 1)[0].strip()
                    # Remove common patterns like (1), (2), etc
                    import re
                    provider_name = re.sub(r'\(\d+\)$', '', provider_name).strip()
            
            # Create ProductPrice entry
            price_entry = ProductPrice(
                product_id=product.id,
                source_file_id=product.source_file_id or 0,
                unit_price=product.unit_price,
                currency=product.currency or "ARS",
                provider_name=provider_name,
                last_seen_at=product.last_seen_at or product.updated_at,
                created_at=product.created_at,
                updated_at=product.updated_at
            )
            session.add(price_entry)
            migrated_count += 1
        
        session.commit()
        session.close()
        print(f"[DB] Migrated {migrated_count} products to ProductPrice table.")
    except Exception as e:
        print(f"[DB] Error during product price migration: {e}")


