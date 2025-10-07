from datetime import datetime
import os
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_engine, get_session, init_db, setup_trgm, setup_fts
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
async def upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    await import_excels(files, db)
    return RedirectResponse(url="/uploads", status_code=303)


@app.post("/uploads/{upload_id}/delete")
def delete_upload(upload_id: int, db: Session = Depends(get_db_session)):
    # Lazy imports
    from .models import Upload, Product

    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload is None:
        return RedirectResponse(url="/uploads", status_code=303)

    # Remove related products then the upload record
    db.query(Product).filter(Product.source_file_id == upload_id).delete(synchronize_session=False)
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
    margin: Optional[float] = None,
    rounding: Optional[str] = None,
    limit: Optional[str] = None,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db_session),
):
    settings = get_or_create_settings(db)
    if product_id is not None:
        # Direct fetch by selected suggestion
        from .models import Product
        p = db.get(Product, product_id)
        if not p:
            return templates.TemplateResponse(
                "partials/results_table.html",
                {"request": request, "results": [], "query": q or "", "margin": margin},
            )
        effective_margin = margin or settings.default_margin_multiplier
        effective_rounding = rounding or settings.rounding_strategy
        final_price = compute_final_price(
            base_price=p.unit_price,
            margin_multiplier=effective_margin,
            rounding_strategy=effective_rounding,
        )
        results_view = [{
            "product": p,
            "score": 100.0,
            "final_price": final_price,
            "final_price_fmt": format_ars(final_price),
            "unit_price_fmt": format_ars(p.unit_price),
        }]
        return templates.TemplateResponse(
            "partials/results_table.html",
            {"request": request, "results": results_view, "query": p.name, "margin": effective_margin},
        )

    if not q or not q.strip():
        # Empty search → empty results fragment
        return templates.TemplateResponse(
            "partials/results_table.html",
            {"request": request, "results": [], "query": q or "", "margin": margin or settings.default_margin_multiplier},
        )

    effective_margin = margin or settings.default_margin_multiplier
    effective_rounding = rounding or settings.rounding_strategy
    try:
        effective_limit = int(limit) if limit not in (None, "") else 50
    except (TypeError, ValueError):
        effective_limit = 50
    results = search_products(query=q, session=db, limit=effective_limit)

    # Augment with final_price for rendering
    results_view = []
    for p, score in results:
        final_price = compute_final_price(
            base_price=p.unit_price,
            margin_multiplier=effective_margin,
            rounding_strategy=effective_rounding,
        )
        results_view.append({
            "product": p,
            "score": score,
            "final_price": final_price,
            "final_price_fmt": format_ars(final_price),
            "unit_price_fmt": format_ars(p.unit_price),
        })

    return templates.TemplateResponse(
        "partials/results_table.html",
        {"request": request, "results": results_view, "query": q, "margin": effective_margin},
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
        results = search_products(query=q, session=db, limit=4)
        suggestions = [{"id": p.id, "name": p.name, "price_fmt": format_ars(p.unit_price), "currency": p.currency} for p, _ in results]
        # cache solo si hay resultados y hay al menos 2 caracteres
        if len(q.strip()) >= 2 and suggestions:
            suggest_cache[key] = suggestions
    return templates.TemplateResponse(
        "partials/suggestions.html",
        {"request": request, "suggestions": suggestions, "query": q},
    )


