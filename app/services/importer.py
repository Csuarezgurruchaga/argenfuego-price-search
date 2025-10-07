from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import Upload, Product
from ..utils.text import normalize_text


def _infer_columns(df: pd.DataFrame) -> dict:
    # Heuristic mapping of possible column names
    lower_cols = {c.lower(): c for c in df.columns}
    name_col = None
    price_col = None
    sku_col: Optional[str] = None
    currency_col: Optional[str] = None

    for key in ["producto", "descripcion", "nombre", "name", "producto_nombre", "item"]:
        if key in lower_cols:
            name_col = lower_cols[key]
            break
    if name_col is None and len(df.columns) >= 1:
        name_col = df.columns[0]

    for key in ["precio", "price", "unit_price", "mayorista", "wholesale", "valor"]:
        if key in lower_cols:
            price_col = lower_cols[key]
            break
    if price_col is None and len(df.columns) >= 2:
        price_col = df.columns[1]

    for key in ["sku", "codigo", "codigo_sku", "code"]:
        if key in lower_cols:
            sku_col = lower_cols[key]
            break

    for key in ["moneda", "currency"]:
        if key in lower_cols:
            currency_col = lower_cols[key]
            break

    return {
        "name": name_col,
        "price": price_col,
        "sku": sku_col,
        "currency": currency_col,
    }


async def import_excels(files: List[UploadFile], session: Session) -> None:
    upload = Upload(filename=", ".join([f.filename for f in files]), uploaded_at=datetime.utcnow())
    session.add(upload)
    session.commit()
    session.refresh(upload)

    total_rows = 0

    for f in files:
        content = await f.read()
        # Use pandas to parse Excel from bytes
        xls = pd.ExcelFile(content)
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            if df.empty:
                continue
            mapping = _infer_columns(df)
            name_col = mapping["name"]
            price_col = mapping["price"]
            sku_col = mapping["sku"]
            currency_col = mapping["currency"]

            for _, row in df.iterrows():
                try:
                    name_val = str(row[name_col]).strip()
                    if name_val == "nan" or name_val == "None":
                        continue
                    price_val = row[price_col]
                    if price_val is None:
                        continue
                    try:
                        price_float = float(price_val)
                    except Exception:
                        continue

                    sku_val = str(row[sku_col]).strip() if sku_col and row.get(sku_col) is not None else None
                    currency_val = str(row[currency_col]).strip() if currency_col and row.get(currency_col) is not None else "ARS"

                    product = Product(
                        sku=sku_val if sku_val else None,
                        name=name_val,
                        normalized_name=normalize_text(name_val),
                        keywords=None,
                        unit_price=round(price_float, 2),
                        currency=currency_val or "ARS",
                        source_file_id=upload.id,
                        last_seen_at=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(product)
                    total_rows += 1
                except Exception:
                    # Skip problematic row but continue
                    continue
            session.commit()

    upload.sheet_count = len(files)
    upload.processed_rows = total_rows
    session.add(upload)
    session.commit()


