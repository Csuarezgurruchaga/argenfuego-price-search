from typing import List, Tuple
from sqlalchemy.orm import Session, joinedload
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

    raw_query = (query or "").lower()
    raw_no_slash = raw_query.replace("/", " ")
    has_manguera_context = any(tok.startswith("manguer") for tok in tokens)

    contains_sin_phrase = (
        "sin sello" in raw_no_slash
        or "sin s" in raw_no_slash
        or raw_no_slash.rstrip().endswith("sin")
        or any(tok == "ssello" for tok in tokens)
    )
    contains_con_phrase = (
        "con sello" in raw_no_slash
        or "con s" in raw_no_slash
        or raw_no_slash.rstrip().endswith("con")
        or "c s" in raw_no_slash
        or any(tok == "csello" for tok in tokens)
    )

    match_tokens = [tok for tok in tokens if tok not in {"sin", "con"}]

    if has_manguera_context and contains_sin_phrase and "ssello" not in match_tokens:
        match_tokens.append("ssello")
    if has_manguera_context and contains_con_phrase and "csello" not in match_tokens:
        match_tokens.append("csello")

    wants_sin = contains_sin_phrase or "ssello" in match_tokens
    wants_con = contains_con_phrase or "csello" in match_tokens

    def with_query_boost(product: Product, base_score: float) -> Tuple[Product, float]:
        bonus = 0.0
        norm_name = product.normalized_name or ""
        has_sin_variant = "ssello" in norm_name
        has_con_variant = "csello" in norm_name
        if wants_sin:
            if has_sin_variant:
                bonus += 20.0
            if has_con_variant:
                bonus -= 15.0
        if wants_con:
            if has_con_variant:
                bonus += 20.0
            if has_sin_variant:
                bonus -= 15.0
        return (product, base_score + bonus)

    # 1. Try Full-Text Search (FTS) with AND for all tokens (most precise)
    if match_tokens:
        try:
            ts_query = " & ".join(match_tokens)
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
                return [with_query_boost(p, 100.0) for p in fts_results]
        except Exception as e:
            # Rollback on error to prevent transaction abort
            session.rollback()
            # Fallback silently if FTS is not supported or fails
            pass

    # 2. Fallback to LIKE with AND for all tokens (still precise)
    if match_tokens:
        like_and_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in match_tokens]
        and_results = (
            session.query(Product)
            .options(joinedload(Product.prices))
            .filter(and_(*like_and_clauses))
            .order_by(Product.updated_at.desc())
            .limit(limit)
            .all()
        )
        if and_results:
            return [with_query_boost(p, 100.0) for p in and_results]

    # 3. Fallback to LIKE with OR for any token (broader match)
    if match_tokens:
        like_or_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in match_tokens]
        or_results = (
            session.query(Product)
            .options(joinedload(Product.prices))
            .filter(or_(*like_or_clauses))
            .order_by(Product.updated_at.desc())
            .limit(limit)
            .all()
        )
        if or_results:
            return [with_query_boost(p, 100.0) for p in or_results]

    # 4. Fallback to fuzzy search (RapidFuzz) if no direct matches
    candidates = session.query(Product).options(joinedload(Product.prices)).order_by(Product.updated_at.desc()).limit(5000).all()
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
            boosted_score = with_query_boost(product, float(score))
            output.append(boosted_score)
    return output
