from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from ..models import Product, ProductPrice
from ..utils.formatting import format_ars
from ..utils.text import compute_final_price
from .search import search_products


@dataclass
class ProviderOffer:
    provider_name: str
    provider_product_name: str
    unit_price: float
    unit_price_fmt: str
    final_price: float
    final_price_fmt: str
    currency: str
    last_seen_at: Optional[datetime]
    source_product_id: int
    source_product_name: str
    canonical_key: Optional[str]
    is_best: bool = False


@dataclass
class VariantResult:
    offers: List[ProviderOffer]
    canonical_key: Optional[str]


def _resolve_search_basis(product: Product, query_text: Optional[str]) -> Optional[str]:
    if query_text and query_text.strip():
        return query_text.strip()
    if product.display_name:
        return product.display_name
    return product.name


def _collect_candidates_from_search(
    session: Session,
    search_basis: Optional[str],
    limit: int,
) -> List[Tuple[Product, float]]:
    if not search_basis:
        return []
    return search_products(query=search_basis, session=session, limit=limit)


def _merge_price_sources(product: Product, prices: List[ProductPrice]) -> List[ProductPrice]:
    """Combine price rows from query with those already attached to product."""
    by_id: dict[int, ProductPrice] = {}
    for price in prices:
        if price.id is not None:
            by_id[price.id] = price
    for price in product.prices:
        if price.id is not None:
            by_id.setdefault(price.id, price)
        else:
            by_id[id(price)] = price
    return list(by_id.values())


def collect_variant_offers(
    session: Session,
    product: Product,
    *,
    iva: float,
    iibb: float,
    profit: float,
    query_text: Optional[str] = None,
    search_limit: int = 40,
    min_similarity: float = 65.0,
) -> VariantResult:
    """
    Aggregate provider offers for a given product. Uses canonical keys when available,
    otherwise falls back to fuzzy search to capture variants sold by other vendors.
    """
    canonical_key = product.canonical_key
    search_basis = _resolve_search_basis(product, query_text)

    search_hits: List[Tuple[Product, float]] = []
    if canonical_key is None:
        search_hits = _collect_candidates_from_search(session, search_basis, search_limit)
        for candidate, _ in search_hits:
            if candidate.canonical_key:
                canonical_key = candidate.canonical_key
                break

    price_query = session.query(ProductPrice).options(joinedload(ProductPrice.product))
    related_prices: List[ProductPrice] = []

    if canonical_key:
        related_prices = (
            price_query
            .filter(ProductPrice.canonical_key == canonical_key)
            .order_by(ProductPrice.provider_name.asc(), ProductPrice.updated_at.desc())
            .all()
        )
    else:
        candidate_ids = {product.id}
        for candidate, score in search_hits:
            if candidate.id == product.id:
                continue
            if score >= min_similarity:
                candidate_ids.add(candidate.id)
        if candidate_ids:
            related_prices = (
                price_query
                .filter(ProductPrice.product_id.in_(list(candidate_ids)))
                .order_by(ProductPrice.provider_name.asc(), ProductPrice.updated_at.desc())
                .all()
            )

    related_prices = _merge_price_sources(product, related_prices)

    if canonical_key is None:
        for price in related_prices:
            if price.canonical_key:
                canonical_key = price.canonical_key
                break

    offers_by_provider: dict[str, ProviderOffer] = {}
    for price in related_prices:
        if price.unit_price is None:
            continue
        provider_name = (price.provider_name or "Proveedor desconocido").strip() or "Proveedor desconocido"
        base_price = float(price.unit_price)
        final_price = compute_final_price(
            base_price=base_price,
            iva=iva,
            iibb=iibb,
            profit=profit,
        )

        provider_product_name = (
            price.provider_product_name
            or (price.product.display_name if price.product and price.product.display_name else None)
            or (price.product.name if price.product else "")
        )

        entry = ProviderOffer(
            provider_name=provider_name,
            provider_product_name=provider_product_name,
            unit_price=round(base_price, 2),
            unit_price_fmt=format_ars(base_price),
            final_price=final_price,
            final_price_fmt=format_ars(final_price),
            currency=price.currency or "ARS",
            last_seen_at=price.updated_at,
            source_product_id=price.product_id,
            source_product_name=price.product.display_name if price.product and price.product.display_name else price.product.name if price.product else provider_product_name,
            canonical_key=price.canonical_key,
        )

        existing = offers_by_provider.get(provider_name)
        if existing is None:
            offers_by_provider[provider_name] = entry
            continue

        better_price = final_price < existing.final_price - 0.005
        same_price_newer = abs(final_price - existing.final_price) <= 0.005 and (
            entry.last_seen_at and (existing.last_seen_at is None or entry.last_seen_at > existing.last_seen_at)
        )
        if better_price or same_price_newer:
            offers_by_provider[provider_name] = entry

    offers = list(offers_by_provider.values())
    offers.sort(key=lambda offer: (offer.final_price, offer.provider_name))

    if offers:
        best_price = offers[0].final_price
        for offer in offers:
            if abs(offer.final_price - best_price) <= 0.01:
                offer.is_best = True
            else:
                break

    return VariantResult(offers=offers, canonical_key=canonical_key)
