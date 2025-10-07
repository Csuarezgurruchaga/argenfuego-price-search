import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str
    default_margin_multiplier: float
    rounding_strategy: str


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if not database_url:
        # Local fallback to SQLite; Railway will set DATABASE_URL for Postgres
        database_url = "sqlite:///./data.db"

    default_margin_str = os.getenv("DEFAULT_MARGIN", "1.5")
    try:
        default_margin = float(default_margin_str)
    except ValueError:
        default_margin = 1.5

    rounding_strategy = os.getenv("ROUNDING_STRATEGY", "none")

    return Settings(
        database_url=database_url,
        default_margin_multiplier=default_margin,
        rounding_strategy=rounding_strategy,
    )


