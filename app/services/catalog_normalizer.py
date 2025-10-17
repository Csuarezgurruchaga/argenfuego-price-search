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
        # Keep normalized name in sync with latest normalization rules
        desired_normalized = normalize_text(product.name)
        if product.normalized_name != desired_normalized:
            product.normalized_name = desired_normalized
            product.updated_at = now
            session.add(product)

        prices = list(product.prices)
        for price in prices:
            source_name = price.provider_product_name or product.name
            match = find_product_match(price.provider_name, source_name, product.sku)
            if not match:
                continue

            canonical_name = match.canonical_name
            canonical_key = match.canonical_key
            norm_name = normalize_text(canonical_name)

            canonical_product = canonical_cache.get(canonical_key)
            if canonical_product is None:
                canonical_product = session.execute(
                    select(Product).where(Product.canonical_key == canonical_key)
                ).scalar_one_or_none()
                if canonical_product is None:
                    canonical_product = session.execute(
                        select(Product).where(Product.normalized_name == norm_name)
                    ).scalar_one_or_none()
                if canonical_product is None:
                    canonical_product = Product(
                        sku=product.sku,
                        canonical_key=canonical_key,
                        name=canonical_name,
                        normalized_name=norm_name,
                        display_name=canonical_name,
                        keywords=None,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(canonical_product)
                    session.flush()
                else:
                    if canonical_product.canonical_key != canonical_key:
                        canonical_product.canonical_key = canonical_key
                    if canonical_product.name != canonical_name:
                        canonical_product.name = canonical_name
                    if not canonical_product.display_name:
                        canonical_product.display_name = canonical_name
                    canonical_product.updated_at = now
                    if product.sku and not canonical_product.sku:
                        canonical_product.sku = product.sku
                canonical_cache[canonical_key] = canonical_product

            if canonical_product.canonical_key != canonical_key:
                canonical_product.canonical_key = canonical_key

            if price.product_id != canonical_product.id:
                price.product_id = canonical_product.id
            if price.canonical_key != canonical_key:
                price.canonical_key = canonical_key
            price.updated_at = now
            session.add(price)

        if product.canonical_key:
            canonical_cache.setdefault(product.canonical_key, product)

    session.flush()

    # Remove products that ended up without precios asociados
    orphan_products = session.query(Product).filter(~Product.prices.any()).all()
    for orphan in orphan_products:
        session.delete(orphan)

    session.flush()
