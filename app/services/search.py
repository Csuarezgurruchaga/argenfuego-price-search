from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from rapidfuzz import fuzz, process

from ..models import Product
from ..utils.text import normalize_text


def search_products(query: str, session: Session, limit: int = 50) -> List[Tuple[Product, float]]:
    """
    Search products by fuzzy matching on normalized name.
    Returns a list of (Product, score) tuples, sorted by relevance.
    """
    norm_q = normalize_text(query)
    if not norm_q:
        return []

    # Preserve special patterns before tokenization
    # Convert "s/sello" → "ssello", "c/sello" → "csello" to make them distinct
    # Also handle "sin sello" → "ssello", "con sello" → "csello"
    norm_q = norm_q.replace("s/sello", "ssello")
    norm_q = norm_q.replace("c/sello", "csello")
    norm_q = norm_q.replace("sin sello", "ssello")
    norm_q = norm_q.replace("con sello", "csello")
    
    # Tokenize and filter stopwords
    stopwords = {"de", "la", "el", "y", "a", "en", "para", "por", "del", "al", "los", "las", "un", "una", "unos", "unas"}
    tokens = [t for t in norm_q.split(" ") if t and t not in stopwords]

    # 1. Try Full-Text Search (FTS) with AND for all tokens (most precise)
    if tokens:
        try:
            ts_query = " & ".join(tokens)
            fts_results = (
                session.query(Product)
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

    # 2. Fallback to LIKE with AND for all tokens (still precise)
    if tokens:
        like_and_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in tokens]
        and_results = (
            session.query(Product)
            .filter(and_(*like_and_clauses))
            .order_by(Product.updated_at.desc())
            .limit(limit)
            .all()
        )
        if and_results:
            return [(p, 100.0) for p in and_results]

    # 3. Fallback to LIKE with OR for any token (broader match)
    if tokens:
        like_or_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in tokens]
        or_results = (
            session.query(Product)
            .filter(or_(*like_or_clauses))
            .order_by(Product.updated_at.desc())
            .limit(limit)
            .all()
        )
        if or_results:
            return [(p, 100.0) for p in or_results]

    # 4. Fallback to fuzzy search (RapidFuzz) if no direct matches
    candidates = session.query(Product).order_by(Product.updated_at.desc()).limit(5000).all()
    if not candidates:
        return []

    choices = {p.id: f"{p.normalized_name} {p.keywords or ''}" for p in candidates}

    results = process.extract(
        norm_q,
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
