import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str
    default_iva: float
    default_iibb: float
    default_profit: float
    default_margin_multiplier: float  # legacy
    rounding_strategy: str  # legacy
    openai_api_key: str | None


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if not database_url:
        # Local fallback to SQLite; Railway will set DATABASE_URL for Postgres
        database_url = "sqlite:///./data.db"
    else:
        # Normalize postgres scheme for SQLAlchemy + psycopg3
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://") and "+" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # New pricing parameters
    default_iva_str = os.getenv("DEFAULT_IVA", "1.21")
    default_iibb_str = os.getenv("DEFAULT_IIBB", "1.025")
    default_profit_str = os.getenv("DEFAULT_PROFIT", "1.0")
    
    try:
        default_iva = float(default_iva_str)
    except ValueError:
        default_iva = 1.21
    
    try:
        default_iibb = float(default_iibb_str)
    except ValueError:
        default_iibb = 1.025
    
    try:
        default_profit = float(default_profit_str)
    except ValueError:
        default_profit = 1.0

    # Legacy parameters
    default_margin_str = os.getenv("DEFAULT_MARGIN", "1.5")
    try:
        default_margin = float(default_margin_str)
    except ValueError:
        default_margin = 1.5

    rounding_strategy = os.getenv("ROUNDING_STRATEGY", "none")
    
    # OpenAI API key for OCR+LLM processing
    openai_api_key = os.getenv("OPENAI_API_KEY")

    return Settings(
        database_url=database_url,
        default_iva=default_iva,
        default_iibb=default_iibb,
        default_profit=default_profit,
        default_margin_multiplier=default_margin,
        rounding_strategy=rounding_strategy,
        openai_api_key=openai_api_key,
    )


