from datetime import datetime
import os
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_engine, get_session, init_db, setup_trgm, setup_fts, migrate_settings_table, migrate_to_product_prices
from .models import Setting
from .services.importer import import_excels
from .services.search import search_products
from .utils.text import compute_final_price
from .utils.formatting import format_ars
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
    # Optional: accelerate LIKE queries on Postgres
    setup_trgm()
    # Enable FTS index if possible
    setup_fts()


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
        from .models import Product, ProductPrice
        from sqlalchemy.orm import joinedload
        p = db.query(Product).options(joinedload(Product.prices)).filter(Product.id == product_id).first()
        if not p:
            return templates.TemplateResponse(
                "partials/results_table.html",
                {"request": request, "results": [], "query": q or ""},
            )
        
        # Build price entries for each provider
        price_entries = []
        for price in p.prices:
            final_price = compute_final_price(
                base_price=price.unit_price,
                iva=effective_iva,
                iibb=effective_iibb,
                profit=effective_profit,
            )
            price_entries.append({
                "provider_name": price.provider_name,
                "unit_price": price.unit_price,
                "unit_price_fmt": format_ars(price.unit_price),
                "final_price": final_price,
                "final_price_fmt": format_ars(final_price),
                "currency": price.currency,
            })
        
        # Sort by final price (cheapest first)
        price_entries.sort(key=lambda x: x["final_price"])
        
        results_view = [{
            "product": p,
            "score": 100.0,
            "prices": price_entries,
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
    results_view = []
    for p, score in results:
        # Build price entries for each provider
        price_entries = []
        for price in p.prices:
            final_price = compute_final_price(
                base_price=price.unit_price,
                iva=effective_iva,
                iibb=effective_iibb,
                profit=effective_profit,
            )
            price_entries.append({
                "provider_name": price.provider_name,
                "unit_price": price.unit_price,
                "unit_price_fmt": format_ars(price.unit_price),
                "final_price": final_price,
                "final_price_fmt": format_ars(final_price),
                "currency": price.currency,
            })
        
        # Sort by final price (cheapest first)
        price_entries.sort(key=lambda x: x["final_price"])
        
        results_view.append({
            "product": p,
            "score": score,
            "prices": price_entries,
        })

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
        suggestions = []
        for p, _ in results:
            # Find cheapest price across all providers
            if p.prices:
                cheapest_price = min(price.unit_price for price in p.prices)
                provider_count = len(p.prices)
                price_label = f"{format_ars(cheapest_price)}"
                if provider_count > 1:
                    price_label += f" ({provider_count} proveedores)"
            else:
                # Fallback for legacy products without prices
                cheapest_price = 0
                price_label = "Sin precio"
            
            suggestions.append({
                "id": p.id,
                "name": p.name,
                "price_fmt": price_label,
                "currency": p.prices[0].currency if p.prices else "ARS"
            })
        
        # cache solo si hay resultados y hay al menos 2 caracteres
        if len(q.strip()) >= 2 and suggestions:
            suggest_cache[key] = suggestions
    return templates.TemplateResponse(
        "partials/suggestions.html",
        {"request": request, "suggestions": suggestions, "query": q},
    )


