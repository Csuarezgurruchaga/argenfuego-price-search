from datetime import datetime
from typing import List, Optional
import json
import io
import os

from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from openai import OpenAI
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Product, ProductPrice
from ..utils.text import normalize_text
from sqlalchemy import select

# Ensure Tesseract knows where to find language data on common macOS setups.
if "TESSDATA_PREFIX" not in os.environ:
    default_tessdata = "/opt/homebrew/share/tessdata"
    if os.path.isdir(default_tessdata):
        os.environ["TESSDATA_PREFIX"] = default_tessdata

DEFAULT_LANGS = ["spa", "eng"]


PRICE_EXTRACTION_PROMPT_TEMPLATE = """Eres un experto en extraer listas de precios de documentos de proveedores mayoristas.

Tu tarea es analizar el siguiente texto extraído por OCR de un documento de precios y convertirlo en una lista estructurada de productos.

IMPORTANTE - REGLAS DE EXTRACCIÓN:
1. **Corrección de errores OCR**: El OCR puede confundir caracteres:
   - Letra "O" (o) por número "0" (cero)
   - Letra "l" (L minúscula) por número "1"
   - Letra "S" por número "5"
   - Espacios faltantes o extras en precios
   
2. **Formato de precios**: 
   - Algunos precios pueden estar en formato argentino: "1.234,56" o "$1.234,56"
   - Otros pueden ser: "1234.56" o "1234,56"
   - Convertir TODO a formato numérico decimal (ej: 1234.56)
   
3. **Filtrado**:
   - IGNORAR: encabezados, títulos, fechas, totales, notas al pie
   - IGNORAR: líneas que no sean productos (ej: "Total: 47 productos", "IVA incluido")
   - SOLO extraer líneas que contengan: nombre de producto + precio
   
4. **Nombres de productos**:
   - Preservar el nombre COMPLETO y EXACTO del producto
   - NO modificar abreviaciones (ej: "C/SELLO" dejarlo así, no expandir)
   - Incluir todas las especificaciones (medidas, materiales, etc.)

5. **Moneda**:
   - Por defecto es "ARS" (pesos argentinos)
   - Si aparece "USD" o "U$S", marcar como "USD"

OUTPUT REQUERIDO:
Devolver ÚNICAMENTE un JSON array válido con este formato exacto:
[
  {{
    "nombre": "NOMBRE COMPLETO DEL PRODUCTO TAL COMO APARECE",
    "precio": 1234.56,
    "moneda": "ARS"
  }}
]

REGLAS CRÍTICAS:
- NO incluir texto explicativo, SOLO el JSON
- NO usar markdown (```json), SOLO el JSON puro
- Precio SIEMPRE como número decimal (float), nunca como string
- Si un precio tiene error obvio (ej: "8.7OO" con letra O), corregirlo a "8700"
- Si no se puede determinar el precio con certeza, omitir ese producto

TEXTO OCR A PROCESAR:
---
{ocr_text}
---

Ahora devuelve el JSON con los productos encontrados:"""


async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using OCR.
    Converts PDF pages to images and applies pytesseract.
    """
    try:
        # Convert PDF to images (one per page)
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        # OCR each page
        full_text = ""
        for i, img in enumerate(images):
            page_text = run_ocr_on_image(img)
            full_text += f"\n--- Página {i+1} ---\n{page_text}"
        
        return full_text.strip()
    except Exception as e:
        print(f"[PDF OCR] Error: {e}")
        return ""


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image (JPEG, PNG, etc.) using OCR.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        text = run_ocr_on_image(img)
        return text.strip()
    except Exception as e:
        print(f"[Image OCR] Error: {e}")
        return ""


def run_ocr_on_image(image: Image.Image) -> str:
    """Try OCR with preferred language list, falling back gracefully."""
    for lang in DEFAULT_LANGS:
        try:
            return pytesseract.image_to_string(image, lang=lang)
        except pytesseract.TesseractError:
            continue
    return pytesseract.image_to_string(image)


def parse_prices_with_gpt4(ocr_text: str, provider_name: str) -> List[dict]:
    """
    Use GPT-4 Turbo to parse OCR text and extract structured product list.
    Returns list of dicts: [{"nombre": "...", "precio": 123.45, "moneda": "ARS"}]
    
    Updated: 2025-10-08 - Added robust JSON extraction with detailed logging
    """
    print("[GPT-4] VERSION CHECK: Using updated code with robust JSON extraction (2025-10-08)")
    settings = get_settings()
    
    if not settings.openai_api_key:
        print("[GPT-4] Warning: OPENAI_API_KEY not set. Skipping LLM parsing.")
    return []


def parse_prices_rule_based(ocr_text: str) -> List[dict]:
    """
    Basic heuristic parser for OCR text.
    Looks for lines with a price token and attempts to split CODE | NAME PRICE.
    """
    results: List[dict] = []
    seen = set()

    def normalize_price_token(token: str) -> Optional[float]:
        token = token.strip()
        if not token:
            return None
        token = token.replace("$", "").replace("ARS", "").replace("USD", "").strip()
        token = token.replace(".", "").replace(",", ".") if token.count(",") == 1 and token.count(".") <= 1 else token
        token = token.replace(" ", "")
        try:
            value = float(token)
            if value <= 0:
                return None
            return round(value, 2)
        except ValueError:
            return None

    for raw_line in ocr_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "precio" in line.lower():
            continue
        lowered = line.lower()
        if "$" not in line and "usd" not in lowered and "ars" not in lowered:
            continue

        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 0:
            parts = [line]

        price_token: Optional[float] = None
        currency = "ARS"
        tokens = parts[-1].split()
        price_index = None
        currency_index = None
        for idx in range(len(tokens) - 1, -1, -1):
            tok = tokens[idx]
            lowered = tok.lower()
            if "usd" in lowered:
                currency = "USD"
                if currency_index is None:
                    currency_index = idx
            candidate = normalize_price_token(tok)
            if candidate is not None:
                price_token = candidate
                price_index = idx
                break
        if price_token is None:
            continue

        name_parts = []
        code = None
        if len(parts) >= 2:
            code = parts[0]
            name_parts = parts[1:]
        else:
            name_parts = [line]

        if price_index is not None:
            clean_tail_tokens = tokens[:price_index]
        else:
            clean_tail_tokens = tokens

        def is_currency_token(tok: str) -> bool:
            stripped = tok.strip().lower()
            return stripped in {"$", "ars", "usd"} or stripped.startswith("$")

        clean_tail_tokens = [
            tok for tok in clean_tail_tokens if not is_currency_token(tok)
        ]

        clean_tail = " ".join(clean_tail_tokens).strip()
        if name_parts:
            name_parts = name_parts[:-1] + ([clean_tail] if clean_tail else [])
        else:
            name_parts = [clean_tail]

        name = " ".join(part for part in name_parts if part).strip()
        if not name:
            continue
        if code:
            normalized_code = code.strip()
            if normalized_code and not name.lower().startswith(normalized_code.lower()):
                name = f"{normalized_code} {name}"
        if sum(ch.isalpha() for ch in name) == 0:
            continue
        if name.lower().startswith("precio"):
            continue

        key = (name.lower(), price_token, currency)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "nombre": name,
                "precio": price_token,
                "moneda": currency,
            }
        )
    return results


def parse_prices_hybrid(ocr_text: str, provider_name: str) -> List[dict]:
    """
    Combine rule-based parsing with LLM when available.
    Only unresolved segments are sent to GPT-4.
    """
    base_results = parse_prices_rule_based(ocr_text)
    if not base_results:
        return parse_prices_with_gpt4(ocr_text, provider_name)

    if not get_settings().openai_api_key:
        return base_results

    captured_names = {entry["nombre"].lower() for entry in base_results}
    pending_lines = []
    for line in ocr_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(name in stripped.lower() for name in captured_names):
            continue
        if "$" not in stripped:
            continue
        pending_lines.append(stripped)

    if not pending_lines:
        return base_results

    llm_results = parse_prices_with_gpt4("\n".join(pending_lines), provider_name)
    merged = base_results[:]
    existing = {(entry["nombre"].lower(), entry["precio"]) for entry in base_results}
    for entry in llm_results:
        key = (entry["nombre"].lower(), entry["precio"])
        if key in existing:
            continue
        merged.append(entry)
    return merged
    
    try:
        print(f"[GPT-4] Initializing OpenAI client...")
        client = OpenAI(api_key=settings.openai_api_key)
        
        print(f"[GPT-4] Calling GPT-4 Turbo with {len(ocr_text)} chars of OCR text...")
        # Call GPT-4 Turbo with the OCR text
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en extracción de datos de listas de precios. Devuelves SOLO JSON válido, sin explicaciones."
                    },
                    {
                        "role": "user",
                        "content": PRICE_EXTRACTION_PROMPT_TEMPLATE.format(ocr_text=ocr_text)
                    }
                ],
                temperature=0,  # Maximum consistency for data extraction
                max_tokens=4000,
            )
        except Exception as api_err:
            print(f"[GPT-4] OpenAI API call failed: {type(api_err).__name__}: {api_err}")
            import traceback
            print(f"[GPT-4] Traceback:")
            traceback.print_exc()
            raise
        
        print(f"[GPT-4] Received response from OpenAI API")
        # Extract JSON from response
        raw_response = response.choices[0].message.content or ""
        raw_response = raw_response.strip()
        print(f"[GPT-4] Raw response length: {len(raw_response)} chars")

        # Helper: try to recover a JSON array from arbitrary model output
        def extract_json_array(text: str) -> str | None:
            import re
            s = text.strip()
            # Strip code fences if present
            if "```" in s:
                # Prefer ```json ... ``` but fallback to first fenced block
                if "```json" in s:
                    try:
                        s = s.split("```json", 1)[1]
                        s = s.split("```", 1)[0]
                    except Exception:
                        pass
                else:
                    try:
                        s = s.split("```", 1)[1]
                        s = s.split("```", 1)[0]
                    except Exception:
                        pass
                s = s.strip()

            # If it already looks like a JSON array, return it
            if s.startswith("[") and s.endswith("]"):
                return s

            # Find first array-like segment
            m = re.search(r"\[\s*\{[\s\S]*?\}\s*\]", s)
            if m:
                return m.group(0)

            # As a last resort, try to collect object blocks and wrap into array
            objs = re.findall(r"\{[\s\S]*?\}", s)
            if objs:
                joined = ",\n".join(objs)
                return f"[{joined}]"
            return None

        json_text = extract_json_array(raw_response)
        if json_text is None:
            # Try a minimal normalization: replace single quotes and fix trailing commas
            tmp = raw_response.replace("'", '"')
            json_text = extract_json_array(tmp)

        if json_text is None:
            # Log full response to help diagnose
            print(f"[GPT-4] Could not extract JSON array.")
            print(f"[GPT-4] Full response ({len(raw_response)} chars):")
            print(raw_response)
            return []

        # Fix common trailing comma before closing bracket
        json_text = json_text.replace(",\n]", "]").replace(", ]", "]")

        # Parse JSON
        try:
            products = json.loads(json_text)
        except json.JSONDecodeError as json_err:
            print(f"[GPT-4] JSON decode error: {json_err}")
            print(f"[GPT-4] Attempted to parse:")
            print(json_text[:1000])
            raise
        
        print(f"[GPT-4] Successfully extracted {len(products)} products from {provider_name}")
        return products
        
    except json.JSONDecodeError as e:
        print(f"[GPT-4] JSON parsing error: {e}")
        print(f"[GPT-4] Raw response: {raw_response[:500]}...")
        return []
    except Exception as e:
        print(f"[GPT-4] Error: {e}")
        return []


async def import_pdf_or_image(
    file_bytes: bytes,
    filename: str,
    upload_id: int,
    provider_name: str,
    session: Session,
) -> int:
    """
    Import products from PDF or image file using OCR + GPT-4.
    Returns number of products imported.
    """
    
    # Step 1: OCR - Extract text from file
    print(f"[OCR] Processing {filename}...")
    
    if filename.lower().endswith('.pdf'):
        ocr_text = await extract_text_from_pdf(file_bytes)
    else:
        ocr_text = extract_text_from_image(file_bytes)
    
    if not ocr_text or len(ocr_text) < 50:
        print(f"[OCR] Warning: Extracted text too short ({len(ocr_text)} chars). Possible OCR failure.")
        return 0
    
    print(f"[OCR] Extracted {len(ocr_text)} characters")
    
    # Step 2: GPT-4 - Parse text into structured product list
    products_data = parse_prices_rule_based(ocr_text)
    if products_data:
        settings = get_settings()
        if settings.openai_api_key:
            print("[Import] Rule-based extracted products; refining with hybrid strategy...")
            products_data = parse_prices_hybrid(ocr_text, provider_name)
        else:
            print(f"[Import] Parsed {len(products_data)} products via rule-based strategy.")
    else:
        print("[Import] Rule-based parser found no products; falling back to GPT-4.")
        products_data = parse_prices_with_gpt4(ocr_text, provider_name)
    
    if not products_data:
        print(f"[Import] No products extracted from {filename}")
        return 0
    
    # Step 3: Insert into database (same logic as Excel import)
    imported_count = 0
    now = datetime.utcnow()
    
    for item in products_data:
        try:
            name_val = item.get("nombre", "").strip()
            precio = item.get("precio")
            moneda = item.get("moneda", "ARS")
            
            if not name_val or precio is None:
                continue
            
            # Ensure precio is float
            try:
                price_float = float(precio)
            except (TypeError, ValueError):
                print(f"[Import] Skipping invalid price for {name_val}: {precio}")
                continue
            
            if price_float <= 0:
                continue
            
            # Normalize product name
            norm_name = normalize_text(name_val)
            
            # Find or create Product
            product = session.execute(
                select(Product).where(Product.normalized_name == norm_name)
            ).scalar_one_or_none()
            
            if product is None:
                product = Product(
                    name=name_val,
                    normalized_name=norm_name,
                    created_at=now,
                    updated_at=now,
                )
                session.add(product)
                session.flush()
            else:
                product.updated_at = now
                session.add(product)
            
            # Find or create ProductPrice for this provider
            existing_price = session.execute(
                select(ProductPrice).where(
                    ProductPrice.product_id == product.id,
                    ProductPrice.provider_name == provider_name
                )
            ).scalar_one_or_none()
            
            if existing_price:
                existing_price.unit_price = round(price_float, 2)
                existing_price.currency = moneda
                existing_price.source_file_id = upload_id
                existing_price.provider_product_name = name_val
                existing_price.last_seen_at = now
                existing_price.updated_at = now
                session.add(existing_price)
            else:
                new_price = ProductPrice(
                    product_id=product.id,
                    source_file_id=upload_id,
                    unit_price=round(price_float, 2),
                    currency=moneda,
                    provider_name=provider_name,
                    provider_product_name=name_val,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_price)
            
            imported_count += 1
            
        except Exception as e:
            print(f"[Import] Error processing product: {e}")
            continue
    
    session.commit()
    print(f"[Import] Successfully imported {imported_count} products from {filename}")
    
    return imported_count
