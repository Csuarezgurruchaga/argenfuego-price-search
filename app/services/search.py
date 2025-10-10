from typing import List, Tuple, Set
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, and_, or_
from rapidfuzz import fuzz, process

from ..models import Product
from ..utils.text import normalize_text
from ..normalization.normalization_rules import apply_provider_normalization


def search_products(query: str, session: Session, limit: int = 50) -> List[Tuple[Product, float]]:
    """
    Search products by fuzzy matching on normalized name.
    Normalizes query using all provider rules to maximize matches.
    Returns a list of (Product, score) tuples, sorted by relevance.
    """
    norm_q = normalize_text(query)
    if not norm_q:
        return []

    # Generate normalized variants for all known providers
    # This ensures we match products regardless of which provider naming style the user uses
    providers = ["LACAR", "INCEN SANIT", "ARD"]
    normalized_variants: Set[str] = set()
    
    for provider in providers:
        variant = apply_provider_normalization(norm_q, provider)
        normalized_variants.add(variant)
    
    # Also add the base normalized query (without provider-specific rules)
    normalized_variants.add(norm_q)
    
    # For backward compatibility, also handle the old sello replacements
    norm_q_legacy = norm_q.replace("s/sello", "ssello")
    norm_q_legacy = norm_q_legacy.replace("c/sello", "csello")
    norm_q_legacy = norm_q_legacy.replace("sin sello", "ssello")
    norm_q_legacy = norm_q_legacy.replace("con sello", "csello")
    normalized_variants.add(norm_q_legacy)
    
    # First, try exact match on any normalized variant (most precise)
    exact_matches = (
        session.query(Product)
        .options(joinedload(Product.prices))
        .filter(Product.normalized_name.in_(normalized_variants))
        .order_by(Product.updated_at.desc())
        .limit(limit)
        .all()
    )
    if exact_matches:
        return [(p, 100.0) for p in exact_matches]
    
    # Tokenize and filter stopwords from the primary variant for fuzzy matching
    stopwords = {"de", "la", "el", "y", "a", "en", "para", "por", "del", "al", "los", "las", "un", "una", "unos", "unas"}
    # Use the most normalized variant (from INCEN SANIT which has assume_sin_sello)
    primary_variant = next(iter(normalized_variants))
    tokens = [t for t in primary_variant.split(" ") if t and t not in stopwords]

    # 2. Try Full-Text Search (FTS) with AND for all tokens (most precise)
    if tokens:
        try:
            ts_query = " & ".join(tokens)
            fts_results = (
                session.query(Product)
                .options(joinedload(Product.prices))
                .filter(text("normalized_name_tsv @@ to_tsquery('simple', :q)"))
                .params(q=ts_query)
                .order_by(Product.updated_at.desc())
                .limit(limit)
                .all()
            )
            if fts_results:
                return [(p, 100.0) for p in fts_results]
        except Exception as e:
            # Rollback on error to prevent transaction abort
            session.rollback()
            # Fallback silently if FTS is not supported or fails
            pass

    # 3. Fallback to LIKE with AND for all tokens (still precise)
    # Use regex word boundaries to distinguish "manga" from "manguera"
    if tokens:
        # Use PostgreSQL regex matching with word boundaries for precise matching
        try:
            regex_and_clauses = [
                Product.normalized_name.op('~*')(rf'\y{t}\y') for t in tokens
            ]
            and_results = (
                session.query(Product)
                .options(joinedload(Product.prices))
                .filter(and_(*regex_and_clauses))
                .order_by(Product.updated_at.desc())
                .limit(limit)
                .all()
            )
            if and_results:
                return [(p, 100.0) for p in and_results]
        except Exception:
            # Fallback to ILIKE if regex not supported (e.g., SQLite)
            session.rollback()
            like_and_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in tokens]
            and_results = (
                session.query(Product)
                .options(joinedload(Product.prices))
                .filter(and_(*like_and_clauses))
                .order_by(Product.updated_at.desc())
                .limit(limit)
                .all()
            )
            if and_results:
                return [(p, 100.0) for p in and_results]

    # 4. Fallback to LIKE with OR for any token (broader match)
    # Use regex word boundaries to distinguish "manga" from "manguera"
    if tokens:
        try:
            regex_or_clauses = [
                Product.normalized_name.op('~*')(rf'\y{t}\y') for t in tokens
            ]
            or_results = (
                session.query(Product)
                .options(joinedload(Product.prices))
                .filter(or_(*regex_or_clauses))
                .order_by(Product.updated_at.desc())
                .limit(limit)
                .all()
            )
            if or_results:
                return [(p, 100.0) for p in or_results]
        except Exception:
            # Fallback to ILIKE if regex not supported (e.g., SQLite)
            session.rollback()
            like_or_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in tokens]
            or_results = (
                session.query(Product)
                .options(joinedload(Product.prices))
                .filter(or_(*like_or_clauses))
                .order_by(Product.updated_at.desc())
                .limit(limit)
                .all()
            )
            if or_results:
                return [(p, 100.0) for p in or_results]

    # 5. Fallback to fuzzy search (RapidFuzz) if no direct matches
    candidates = session.query(Product).options(joinedload(Product.prices)).order_by(Product.updated_at.desc()).limit(5000).all()
    if not candidates:
        return []

    choices = {p.id: f"{p.normalized_name} {p.keywords or ''}" for p in candidates}

    results = process.extract(
        primary_variant,
        choices,
        scorer=fuzz.token_set_ratio,
        limit=limit,
        score_cutoff=40,
    )

    id_to_product = {p.id: p for p in candidates}
    output: List[Tuple[Product, float]] = []
    for key, score, _ in results:
        product = id_to_product.get(key)
        if product is not None:
            output.append((product, float(score)))
    return output
