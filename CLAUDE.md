# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArgenFuego Quick Search is a FastAPI web application for managing fire safety equipment price lists. Users upload Excel/PDF files containing product catalogs from multiple providers, then search products with fuzzy matching and calculate final prices with configurable margins.

**Key Challenge**: Different providers use inconsistent naming conventions for identical products (e.g., "MANGUERA S/SELLO 44,5mm" vs "MANGUERA 44.5mm" vs "MANG ARJET 1 1/2"). The system normalizes these to enable cross-provider product matching and price comparison.

## Development Commands

### Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run dev server
export DEFAULT_MARGIN=1.5
uvicorn app.main:app --reload

# Run normalization tests
python test_normalization.py
```

### Database
- Local: Uses SQLite (`./data.db`) when `DATABASE_URL` is not set
- Production: PostgreSQL via Railway (auto-configured via `DATABASE_URL` env var)

## Architecture

### Multi-Provider Product Matching System

The core architecture enables matching products across providers despite naming variations:

1. **Product Model** (`app/models.py`):
   - `Product`: Canonical product entity with `normalized_name` (deduplication key)
   - `ProductPrice`: Per-provider pricing (one Product → many ProductPrices)
   - `Upload`: Tracks source files and provider extraction

2. **Normalization Pipeline** (executed in order):
   - **Step 1**: `app/utils/text.normalize_text()` - General normalization (unidecode, lowercase, special char handling)
   - **Step 2**: `app/normalization/normalization_rules.apply_provider_normalization()` - Provider-specific rules

3. **Provider Rules** (`app/normalization/normalization_rules.py`):
   - `PROVIDER_RULES` dict maps provider name → normalization config
   - Each provider has: `replacements`, `remove_patterns`, `defaults`
   - **Critical rules**:
     - LACAR: Explicit "S/SELLO" vs "C/SELLO" distinction preserved
     - INCEN SANIT: Assumes "sin sello" if not mentioned (`assume_sin_sello: True`)
     - ARD: Converts brand names (RYLJET=con sello, ARJET=sin sello), handles fractional inches
   - **Canonical normalization** (final pass): Synonyms (MANG→MANGUERA, BOQ→BOQUILLA), abbreviations (s/pta→sinpuerta), fractional inches→decimal

4. **Search Engine** (`app/services/search.py`):
   - Generates normalized variants for all known providers from user query
   - Cascading search strategy (fastest to slowest):
     1. Exact match on normalized variants
     2. PostgreSQL Full-Text Search (FTS) with AND logic
     3. LIKE queries with AND logic (all tokens match)
     4. LIKE queries with OR logic (any token matches)
     5. RapidFuzz fuzzy matching (fallback, score_cutoff=40)
   - Uses `pg_trgm` GIN index for ILIKE performance on PostgreSQL

5. **Import Pipeline** (`app/services/importer.py`):
   - Accepts Excel (.xlsx, .xls) and PDF/images (.pdf, .jpg, .png)
   - Heuristic column detection (`_infer_columns`, `choose_price_and_name`, `find_header_row`)
   - Extracts provider name from filename (first file in upload batch)
   - For each row: `_process_product_row()` finds/creates Product by normalized_name, then creates/updates ProductPrice

### Pricing Calculation

**Current System** (`app/utils/text.compute_final_price()`):
- Formula: `base_price * IVA * IIBB * Profit`
- Env vars: `DEFAULT_IVA` (1.21), `DEFAULT_IIBB` (1.025), `DEFAULT_PROFIT` (1.0)
- Legacy support: `DEFAULT_MARGIN` (multiplier), `ROUNDING_STRATEGY` (none/nearest_10/ceil_10/floor_10)

### Database Migrations

Auto-migrations run on startup (`app/main.py:on_startup()`):
- `migrate_settings_table()`: Adds new pricing columns (IVA, IIBB, Profit) to settings
- `migrate_to_product_prices()`: Migrates legacy Product.unit_price → ProductPrice table
- `setup_trgm()`: Creates `pg_trgm` extension + GIN index for fast ILIKE
- `setup_fts()`: Creates tsvector column + GIN index for full-text search

## Testing

**Normalization Tests** (`test_normalization.py`):
- Verifies multi-provider products normalize to identical canonical names
- Test cases cover: different formats (44.5mm vs 44,5mm), abbreviations (MANG vs MANGUERA), provider-specific syntax (ARJET vs S/SELLO)
- Run after modifying `PROVIDER_RULES` to verify product matching still works

## Important Patterns

### Adding a New Provider

1. Add entry to `PROVIDER_RULES` in `app/normalization/normalization_rules.py`
2. Define `replacements`, `remove_patterns`, and `defaults` based on provider's naming conventions
3. Add provider to `providers` list in `app/services/search.py:search_products()` (line 23)
4. Add test cases to `test_normalization.py` covering provider's unique syntax
5. Run `python test_normalization.py` to verify existing products still match

### Modifying Normalization Rules

**CRITICAL**: Changes to normalization affect product deduplication. Test thoroughly:
1. Edit rules in `app/normalization/normalization_rules.py`
2. Run `python test_normalization.py` - all tests must pass
3. Consider impact on existing database (products may split/merge after re-import)

### Adding New Product Synonyms

To normalize "EXTINTOR" → "MATAFUEGO":
1. Add to `PROVIDER_RULES["_DEFAULT"]["replacements"]`: `(r'\bextintor\b', 'matafuego')`
2. Or add to canonical normalization section (line 149+) if it applies across all providers

## Environment Variables

Required in production:
- `DATABASE_URL`: PostgreSQL connection string (auto-provided by Railway)
- `OPENAI_API_KEY`: For PDF/image OCR processing (optional, only needed for PDF uploads)

Optional configuration:
- `DEFAULT_IVA`: Tax multiplier (default: 1.21)
- `DEFAULT_IIBB`: Tax multiplier (default: 1.025)
- `DEFAULT_PROFIT`: Profit margin multiplier (default: 1.0)
- `DEFAULT_MARGIN`: Legacy margin multiplier (default: 1.5)
- `ROUNDING_STRATEGY`: Legacy rounding (none|nearest_10|ceil_10|floor_10, default: none)

## Deployment (Railway)

1. Create PostgreSQL service
2. Create Web service from repo
3. Set environment variables (above)
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Railway auto-detects `requirements.txt` and builds with Nixpacks

**Railway-specific files**:
- `railway.toml`: Build/deploy config
- `nixpacks.toml`: Python version and build settings
- `Aptfile`: System dependencies for Tesseract OCR
- `Procfile`: Alternative start command
