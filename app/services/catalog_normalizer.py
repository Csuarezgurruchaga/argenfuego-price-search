from __future__ import annotations

from datetime import datetime
from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Product
from ..utils.text import normalize_text
from .vendor_dictionary import find_product_match


def normalize_catalog(session: Session) -> None:
    """Merge proveedor variantes that map to the same catálogo canon."""
    canonical_cache: Dict[str, Product] = {}

    products = session.query(Product).options(selectinload(Product.prices)).all()
    now = datetime.utcnow()

    for product in products:
        prices = list(product.prices)
        for price in prices:
            source_name = price.provider_product_name or product.name
            canonical = find_product_match(price.provider_name, source_name, product.sku)
            if not canonical:
                continue

            norm_name = normalize_text(canonical)
            canonical_product = canonical_cache.get(norm_name)
            if canonical_product is None:
                canonical_product = session.execute(
                    select(Product).where(Product.normalized_name == norm_name)
                ).scalar_one_or_none()
                if canonical_product is None:
                    canonical_product = Product(
                        sku=product.sku,
                        name=canonical,
                        normalized_name=norm_name,
                        display_name=canonical,
                        keywords=None,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(canonical_product)
                    session.flush()
                else:
                    if canonical_product.name != canonical:
                        canonical_product.name = canonical
                    if not canonical_product.display_name:
                        canonical_product.display_name = canonical
                    canonical_product.updated_at = now
                    if product.sku and not canonical_product.sku:
                        canonical_product.sku = product.sku
                canonical_cache[norm_name] = canonical_product

            if price.product_id != canonical_product.id:
                price.product_id = canonical_product.id
                price.updated_at = now
                session.add(price)

    session.flush()

    # Remove products that ended up without precios asociados
    orphan_products = session.query(Product).filter(~Product.prices.any()).all()
    for orphan in orphan_products:
        session.delete(orphan)

    session.flush()
