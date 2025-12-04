from datetime import datetime
import os
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import get_settings
from .db import (
    get_engine,
    get_session,
    init_db,
    setup_trgm,
    setup_fts,
    migrate_settings_table,
    migrate_to_product_prices,
    migrate_add_display_name,
    migrate_add_provider_product_name,
    migrate_add_canonical_keys,
)
from .services.catalog_normalizer import normalize_catalog
from .models import Setting
from .services.importer import import_excels
from .services.search import search_products
from .services.variant_resolver import collect_variant_offers
from .services.suggest_cache import suggest_cache, cache_key


app = FastAPI(title="ArgenFuego Quick Search")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.on_event("startup")
def on_startup() -> None:
    # Initialize DB and create tables
    init_db(get_engine())
    # Migrate settings table to add new pricing columns
    migrate_settings_table()
    # Migrate existing products to ProductPrice model
    migrate_to_product_prices()
    # Add display_name column to products table
    migrate_add_display_name()
    # Ensure price table stores proveedor descriptions
    migrate_add_provider_product_name()
    # Ensure canonical grouping key columns exist
    migrate_add_canonical_keys()
    # Optional: accelerate LIKE queries on Postgres
    setup_trgm()
    # Enable FTS index if possible
    setup_fts()
    # Normalize catalog so synonyms point to unificados
    with get_session() as session:
        normalize_catalog(session)


def get_db_session():
    with get_session() as session:
        yield session


def get_or_create_settings(session: Session) -> Setting:
    settings = session.query(Setting).first()
    if settings is None:
        defaults = get_settings()
        settings = Setting(
            default_iva=defaults.default_iva,
            default_iibb=defaults.default_iibb,
            default_profit=defaults.default_profit,
            default_margin_multiplier=defaults.default_margin_multiplier,
            rounding_strategy=defaults.rounding_strategy,
            updated_at=datetime.utcnow(),
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@app.get("/debug/static")
def debug_static():
    """Debug endpoint to check static files"""
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    files = []
    if os.path.exists(static_dir):
        files = os.listdir(static_dir)
    return {
        "static_dir": static_dir,
        "exists": os.path.exists(static_dir),
        "files": files,
        "logo_exists": os.path.exists(os.path.join(static_dir, "logo.png"))
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db_session)):
    settings = get_or_create_settings(db)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_margin": settings.default_margin_multiplier,
            "rounding_strategy": settings.rounding_strategy,
        },
    )


@app.get("/uploads", response_class=HTMLResponse)
def uploads_page(request: Request, db: Session = Depends(get_db_session)):
    # Lazy import to avoid circulars
    from .models import Upload

    uploads = db.query(Upload).order_by(Upload.uploaded_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "uploads.html",
        {"request": request, "uploads": uploads},
    )


@app.post("/upload")
async def upload(request: Request, files: List[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    await import_excels(files, db)
    # Check if request is from HTMX (for AJAX uploads)
    if request.headers.get("HX-Request"):
        return {"status": "success", "message": "Files uploaded successfully"}
    # Fallback to redirect for non-HTMX requests
    return RedirectResponse(url="/uploads", status_code=303)


@app.post("/uploads/{upload_id}/delete")
def delete_upload(upload_id: int, db: Session = Depends(get_db_session)):
    # Lazy imports
    from .models import Upload, ProductPrice

    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload is None:
        return RedirectResponse(url="/uploads", status_code=303)

    # Remove related product prices (cascade will handle this if configured, but being explicit)
    db.query(ProductPrice).filter(ProductPrice.source_file_id == upload_id).delete(synchronize_session=False)
    
    # Delete the upload record
    db.delete(upload)
    db.commit()
    return RedirectResponse(url="/uploads", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db_session)):
    settings = get_or_create_settings(db)
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "default_margin": settings.default_margin_multiplier,
            "rounding_strategy": settings.rounding_strategy,
        },
    )


@app.post("/settings")
def update_settings(
    request: Request,
    default_margin: float = Form(...),
    rounding_strategy: str = Form("none"),
    db: Session = Depends(get_db_session),
):
    settings = get_or_create_settings(db)
    settings.default_margin_multiplier = default_margin
    settings.rounding_strategy = rounding_strategy
    settings.updated_at = datetime.utcnow()
    db.add(settings)
    db.commit()
    return RedirectResponse(url="/settings", status_code=303)


@app.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    q: Optional[str] = None,
    iva: Optional[float] = None,
    iibb: Optional[float] = None,
    profit: Optional[float] = None,
    margin: Optional[float] = None,  # legacy
    rounding: Optional[str] = None,  # legacy
    limit: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db_session),
):
    settings = get_or_create_settings(db)
    
    # Parse new pricing parameters
    effective_iva = iva if iva is not None else 1.21
    effective_iibb = iibb if iibb is not None else 1.025
    effective_profit = profit if profit is not None else 1.0

    if product_id is not None:
        # Direct fetch by selected suggestion
        from .models import Product
        from sqlalchemy.orm import joinedload
        p = db.query(Product).options(joinedload(Product.prices)).filter(Product.id == product_id).first()
        if not p:
            return templates.TemplateResponse(
                "partials/results_table.html",
                {"request": request, "results": [], "query": q or ""},
            )

        variant_result = collect_variant_offers(
            session=db,
            product=p,
            iva=effective_iva,
            iibb=effective_iibb,
            profit=effective_profit,
            query_text=q,
        )

        results_view = [{
            "product": p,
            "score": 100.0,
            "prices": variant_result.offers,
        }]
        return templates.TemplateResponse(
            "partials/results_table.html",
            {"request": request, "results": results_view, "query": p.name},
        )

    if not q or not q.strip():
        # Empty search → empty results fragment
        return templates.TemplateResponse(
            "partials/results_table.html",
            {"request": request, "results": [], "query": q or ""},
        )

    try:
        effective_limit = int(limit) if limit not in (None, "") else 50
    except (TypeError, ValueError):
        effective_limit = 50
    results = search_products(query=q, session=db, limit=effective_limit)

    # Augment with final_price for rendering
    results_view_map = {}
    for p, score in results:
        variant_result = collect_variant_offers(
            session=db,
            product=p,
            iva=effective_iva,
            iibb=effective_iibb,
            profit=effective_profit,
            query_text=q,
        )

        canonical_key = variant_result.canonical_key or p.canonical_key or f"product-{p.id}"
        existing = results_view_map.get(canonical_key)
        if existing is None or score > existing["score"]:
            results_view_map[canonical_key] = {
                "product": p,
                "score": score,
                "prices": variant_result.offers,
            }

    results_view = list(results_view_map.values())
    results_view.sort(key=lambda entry: entry["score"], reverse=True)

    return templates.TemplateResponse(
        "partials/results_table.html",
        {"request": request, "results": results_view, "query": q},
    )


@app.get("/suggest", response_class=HTMLResponse)
def suggest(
    request: Request,
    q: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    if not q or not q.strip():
        return templates.TemplateResponse(
            "partials/suggestions.html",
            {"request": request, "suggestions": []},
        )

    key = cache_key(q)
    if len(q.strip()) >= 2 and key in suggest_cache:
        suggestions = suggest_cache[key]
    else:
        results = search_products(query=q, session=db, limit=20)  # Show top 20 with scroll
        suggestions_map = {}
        for p, _ in results:
            variant_result = collect_variant_offers(
                session=db,
                product=p,
                iva=1.0,
                iibb=1.0,
                profit=1.0,
                query_text=None,
                search_limit=25,
            )
            offers = variant_result.offers

            if offers:
                cheapest_offer = offers[0]
                provider_count = len(offers)
                price_label = cheapest_offer.unit_price_fmt
                if provider_count > 1:
                    price_label += f" ({provider_count} proveedores)"
                currency = cheapest_offer.currency
            else:
                price_label = "Sin precio"
                currency = p.prices[0].currency if p.prices else "ARS"
            
            canonical_key = variant_result.canonical_key or p.canonical_key or f"product-{p.id}"
            if canonical_key in suggestions_map:
                continue
            suggestions_map[canonical_key] = {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name if p.display_name else p.name,
                "price_fmt": price_label,
                "currency": currency,
            }

        suggestions = list(suggestions_map.values())
        
        # cache solo si hay resultados y hay al menos 2 caracteres
        if len(q.strip()) >= 2 and suggestions:
            suggest_cache[key] = suggestions
    return templates.TemplateResponse(
        "partials/suggestions.html",
        {"request": request, "suggestions": suggestions, "query": q},
    )
