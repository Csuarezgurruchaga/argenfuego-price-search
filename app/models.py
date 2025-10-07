from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sheet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    processed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="upload")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="ARS")
    source_file_id: Mapped[int] = mapped_column(ForeignKey("uploads.id"), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    upload: Mapped[Upload] = relationship("Upload", back_populates="products")

    __table_args__ = (
        Index("ix_products_norm_name", "normalized_name"),
    )


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # New pricing parameters
    default_iva: Mapped[float] = mapped_column(Float, nullable=False, default=1.21)
    default_iibb: Mapped[float] = mapped_column(Float, nullable=False, default=1.025)
    default_profit: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    # Legacy parameters (kept for backwards compatibility)
    default_margin_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.5)
    rounding_strategy: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


