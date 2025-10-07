from typing import List, Tuple

from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session

from ..models import Product
from ..utils.text import normalize_text


def search_products(query: str, session: Session, limit: int = 50) -> List[Tuple[Product, float]]:
    norm_q = normalize_text(query)
    if not norm_q:
        return []

    # Fetch a candidate pool (could be improved with LIKE/trigram)
    candidates = session.query(Product).limit(5000).all()
    choices = {p.id: f"{p.normalized_name} {p.keywords or ''}" for p in candidates}

    # Use RapidFuzz to score
    results = process.extract(
        norm_q,
        choices,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=60,
    )
    # results: List[Tuple[key, score, _]] with key being product.id

    id_to_product = {p.id: p for p in candidates}
    output: List[Tuple[Product, float]] = []
    for key, score, _ in results:
        product = id_to_product.get(key)
        if product is not None:
            output.append((product, float(score)))
    return output


