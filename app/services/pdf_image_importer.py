from datetime import datetime
from typing import List, Optional
import json
import io
import tempfile
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


PRICE_EXTRACTION_PROMPT = """Eres un experto en extraer listas de precios de documentos de proveedores mayoristas.

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
  {
    "nombre": "NOMBRE COMPLETO DEL PRODUCTO TAL COMO APARECE",
    "precio": 1234.56,
    "moneda": "ARS"
  }
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
            page_text = pytesseract.image_to_string(img, lang='spa')
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
        text = pytesseract.image_to_string(img, lang='spa')
        return text.strip()
    except Exception as e:
        print(f"[Image OCR] Error: {e}")
        return ""


def parse_prices_with_gpt4(ocr_text: str, provider_name: str) -> List[dict]:
    """
    Use GPT-4 Turbo to parse OCR text and extract structured product list.
    Returns list of dicts: [{"nombre": "...", "precio": 123.45, "moneda": "ARS"}]
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        print("[GPT-4] Warning: OPENAI_API_KEY not set. Skipping LLM parsing.")
        return []
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Call GPT-4 Turbo with the OCR text
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en extracción de datos de listas de precios. Devuelves SOLO JSON válido, sin explicaciones."
                },
                {
                    "role": "user",
                    "content": PRICE_EXTRACTION_PROMPT.format(ocr_text=ocr_text)
                }
            ],
            temperature=0,  # Maximum consistency for data extraction
            max_tokens=4000,
        )
        
        # Extract JSON from response
        raw_response = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        products = json.loads(raw_response)
        
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
    print(f"[GPT-4] Parsing products...")
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

