from typing import List, Tuple

from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import Product
from ..utils.text import normalize_text


def search_products(query: str, session: Session, limit: int = 50, require_all_tokens: bool = False) -> List[Tuple[Product, float]]:
    norm_q = normalize_text(query)
    if not norm_q:
        return []

    # Prefiltro con LIKE por tokens del query
    stopwords = {"de","la","el","y","a","en","para","por","del","al","con","sin","los","las","un","una","unos","unas"}
    tokens = [t for t in norm_q.split(" ") if t and t not in stopwords]
    qset = session.query(Product)
    if tokens:
        like_clauses = [Product.normalized_name.ilike(f"%{t}%") for t in tokens]
        if require_all_tokens:
            qset = qset.filter(and_(*like_clauses))
        else:
            qset = qset.filter(or_(*like_clauses))
        if not require_all_tokens:
            direct = qset.order_by(Product.updated_at.desc()).limit(limit).all()
            if direct:
                return [(p, 100.0) for p in direct]
    candidates = qset.limit(5000).all()

    # Si el prefiltro no encontró nada, prueba con ALL tokens (AND) para queries cortos como "balde camion"
    if not tokens:
        pass
    elif not session.query(Product.id).filter(qset.whereclause).first():
        qset_all = session.query(Product).filter(and_(*[Product.normalized_name.ilike(f"%{t}%") for t in tokens]))
        direct_all = qset_all.order_by(Product.updated_at.desc()).limit(limit).all()
        if direct_all:
            return [(p, 100.0) for p in direct_all]

    # Si el prefiltro no encontró nada, tomar un pool más amplio
    if not candidates:
        candidates = session.query(Product).limit(5000).all()

    choices = {p.id: f"{p.normalized_name} {p.keywords or ''}" for p in candidates}

    # Scoring más tolerante a desorden/typos
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


