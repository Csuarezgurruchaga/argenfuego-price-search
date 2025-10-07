from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import UploadFile
from openpyxl import load_workbook
from sqlalchemy.orm import Session
from xlrd import open_workbook

from ..models import Upload, Product
from ..utils.text import normalize_text


def _infer_columns(headers: List[str]) -> dict:
    lower_cols = {c.strip().lower(): c for c in headers if c is not None}
    name_col = None
    price_col = None
    sku_col: Optional[str] = None
    currency_col: Optional[str] = None

    for key in ["producto", "descripcion", "nombre", "name", "producto_nombre", "item"]:
        if key in lower_cols:
            name_col = lower_cols[key]
            break
    if name_col is None and len(headers) >= 1:
        name_col = headers[0]

    for key in ["precio", "price", "unit_price", "mayorista", "wholesale", "valor"]:
        if key in lower_cols:
            price_col = lower_cols[key]
            break
    if price_col is None and len(headers) >= 2:
        price_col = headers[1]

    for key in ["sku", "codigo", "codigo_sku", "code"]:
        if key in lower_cols:
            sku_col = lower_cols[key]
            break

    for key in ["moneda", "currency"]:
        if key in lower_cols:
            currency_col = lower_cols[key]
            break

    return {"name": name_col, "price": price_col, "sku": sku_col, "currency": currency_col}


async def import_excels(files: List[UploadFile], session: Session) -> None:
    upload = Upload(filename=", ".join([f.filename for f in files]), uploaded_at=datetime.utcnow())
    session.add(upload)
    session.commit()
    session.refresh(upload)

    total_rows = 0
    total_sheets = 0

    for f in files:
        content = await f.read()
        fname = (f.filename or "").lower()

        if fname.endswith(".xls"):
            # Parse legacy .xls via xlrd
            book = open_workbook(file_contents=content)
            for sheet in book.sheets():
                total_sheets += 1
                if sheet.nrows == 0:
                    continue
                headers = [str(sheet.cell_value(0, c)).strip() if sheet.cell_value(0, c) is not None else None for c in range(sheet.ncols)]
                mapping = _infer_columns(headers)
                name_col = mapping["name"]
                price_col = mapping["price"]
                sku_col = mapping["sku"]
                currency_col = mapping["currency"]
                header_index = {h: i for i, h in enumerate(headers) if h is not None}

                for r in range(1, sheet.nrows):
                    try:
                        row = [sheet.cell_value(r, c) for c in range(sheet.ncols)]
                        if name_col is None or price_col is None:
                            continue
                        name_idx = header_index.get(name_col)
                        price_idx = header_index.get(price_col)
                        if name_idx is None or price_idx is None:
                            continue
                        name_cell = row[name_idx] if name_idx < len(row) else None
                        price_cell = row[price_idx] if price_idx < len(row) else None
                        if name_cell is None or str(name_cell).strip() in ("", "nan", "None"):
                            continue
                        if price_cell is None:
                            continue
                        try:
                            price_float = float(price_cell)
                        except Exception:
                            continue

                        sku_val = None
                        if sku_col is not None and header_index.get(sku_col) is not None:
                            sku_idx = header_index[sku_col]
                            if sku_idx < len(row) and row[sku_idx] is not None:
                                sku_val = str(row[sku_idx]).strip()

                        currency_val = "ARS"
                        if currency_col is not None and header_index.get(currency_col) is not None:
                            cur_idx = header_index[currency_col]
                            if cur_idx < len(row) and row[cur_idx] is not None:
                                currency_val = str(row[cur_idx]).strip() or "ARS"

                        name_val = str(name_cell).strip()
                        product = Product(
                            sku=sku_val if sku_val else None,
                            name=name_val,
                            normalized_name=normalize_text(name_val),
                            keywords=None,
                            unit_price=round(price_float, 2),
                            currency=currency_val,
                            source_file_id=upload.id,
                            last_seen_at=datetime.utcnow(),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        session.add(product)
                        total_rows += 1
                    except Exception:
                        continue
                session.commit()
        else:
            # Default to .xlsx via openpyxl
            wb = load_workbook(BytesIO(content), data_only=True)
            for ws in wb.worksheets:
                total_sheets += 1
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    continue
                headers = [str(h).strip() if h is not None else None for h in rows[0]]
                mapping = _infer_columns(headers)
                name_col = mapping["name"]
                price_col = mapping["price"]
                sku_col = mapping["sku"]
                currency_col = mapping["currency"]

                header_index = {h: i for i, h in enumerate(headers) if h is not None}

                for row in rows[1:]:
                    try:
                        if name_col is None or price_col is None:
                            continue
                        name_idx = header_index.get(name_col)
                        price_idx = header_index.get(price_col)
                        if name_idx is None or price_idx is None:
                            continue
                        name_cell = row[name_idx] if name_idx < len(row) else None
                        price_cell = row[price_idx] if price_idx < len(row) else None
                        if name_cell is None or str(name_cell).strip() in ("", "nan", "None"):
                            continue
                        if price_cell is None:
                            continue
                        try:
                            price_float = float(price_cell)
                        except Exception:
                            continue

                        sku_val = None
                        if sku_col is not None and header_index.get(sku_col) is not None:
                            sku_idx = header_index[sku_col]
                            if sku_idx < len(row) and row[sku_idx] is not None:
                                sku_val = str(row[sku_idx]).strip()

                        currency_val = "ARS"
                        if currency_col is not None and header_index.get(currency_col) is not None:
                            cur_idx = header_index[currency_col]
                            if cur_idx < len(row) and row[cur_idx] is not None:
                                currency_val = str(row[cur_idx]).strip() or "ARS"

                        name_val = str(name_cell).strip()
                        product = Product(
                            sku=sku_val if sku_val else None,
                            name=name_val,
                            normalized_name=normalize_text(name_val),
                            keywords=None,
                            unit_price=round(price_float, 2),
                            currency=currency_val,
                            source_file_id=upload.id,
                            last_seen_at=datetime.utcnow(),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        session.add(product)
                        total_rows += 1
                    except Exception:
                        continue
                session.commit()

    upload.sheet_count = total_sheets
    upload.processed_rows = total_rows
    session.add(upload)
    session.commit()


