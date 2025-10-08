# 🔥 Feature: Soporte para PDF, JPG, PNG (OCR + GPT-4 Turbo)

## 📋 Resumen

Esta feature agrega soporte para **importar listas de precios desde PDFs e imágenes** usando:
- **OCR (pytesseract)**: Extrae texto de PDFs/imágenes
- **GPT-4 Turbo**: Parsea y estructura el texto en JSON con alta precisión

## ✨ Funcionalidades

### Formatos Soportados
- ✅ `.xlsx` (Excel moderno) - **Existente**
- ✅ `.xls` (Excel antiguo) - **Existente**
- 🆕 `.pdf` (documentos PDF)
- 🆕 `.jpg`, `.jpeg` (imágenes JPEG)
- 🆕 `.png` (imágenes PNG)

### Flujo de Trabajo

```
Usuario sube PDF/JPEG
    ↓
Backend detecta extensión
    ↓
OCR (pytesseract) extrae texto
    ↓
GPT-4 Turbo parsea → JSON
    ↓
Insert en PostgreSQL (igual que Excel)
    ↓
Búsqueda normal desde DB
```

**Nota**: OCR+LLM se ejecuta **UNA SOLA VEZ** al momento de la carga. Después todo es búsqueda normal en DB.

## 🛠️ Cambios Técnicos

### Nuevos Archivos
- `app/services/pdf_image_importer.py`: Lógica de OCR + GPT-4
- `Aptfile`: Dependencias del sistema para Railway (poppler, tesseract)
- `FEATURE_OCR_LLM.md`: Esta documentación

### Archivos Modificados
- `requirements.txt`: Agregadas librerías (Pillow, pdf2image, pytesseract, openai)
- `app/config.py`: Agregado `openai_api_key` a Settings
- `app/services/importer.py`: Integración de `import_pdf_or_image()`
- `app/templates/index.html`: Accept `.pdf,.jpg,.jpeg,.png` en input

### Nuevas Dependencias

**Python:**
```txt
Pillow==10.4.0
pdf2image==1.17.0
pytesseract==0.3.13
openai==1.54.0
```

**Sistema (Railway):**
```
poppler-utils      # Para pdf2image
tesseract-ocr      # OCR engine
tesseract-ocr-spa  # Lenguaje español
```

## ⚙️ Configuración

### Variable de Entorno Requerida

```bash
# Railway > Variables
OPENAI_API_KEY=sk-...
```

Sin esta variable, los PDFs/imágenes se **ignorarán** (con warning en logs).

## 🎯 Prompt GPT-4 Turbo

El prompt está optimizado para:
- ✅ Corregir errores OCR comunes (O→0, l→1, S→5)
- ✅ Manejar formatos de precios argentinos ($1.234,56)
- ✅ Filtrar headers, footers, notas
- ✅ Devolver JSON estructurado puro
- ✅ Maximum consistency (`temperature=0`)

Ver código completo en `app/services/pdf_image_importer.py` líneas 20-72.

## 💰 Costos Estimados

| Volumen | Costo/mes (GPT-4 Turbo) |
|---------|-------------------------|
| 50 páginas | ~$0.25 - $0.50 |
| 150 páginas | $0.75 - $1.50 |
| 500 páginas | $2.50 - $5.00 |

**Nota**: OCR (pytesseract) es **gratis** (corre local/en Railway).

## 🧪 Testing Local

### 1. Instalar Dependencias del Sistema

**macOS:**
```bash
brew install poppler tesseract tesseract-lang
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-spa
```

### 2. Instalar Dependencias Python

```bash
pip install -r requirements.txt
```

### 3. Configurar API Key

```bash
export OPENAI_API_KEY=sk-...
```

### 4. Ejecutar App

```bash
uvicorn app.main:app --reload
```

### 5. Probar Upload

1. Ir a http://localhost:8000
2. Arrastrar un PDF o JPEG con lista de precios
3. Ver logs en terminal:
   ```
   [OCR] Processing ejemplo.pdf...
   [OCR] Extracted 2345 characters
   [GPT-4] Parsing products...
   [GPT-4] Successfully extracted 47 products from LACAR AGOSTO
   [Import] Successfully imported 47 products from ejemplo.pdf
   ```

## 🚀 Deployment a Railway

### Variables de Entorno

Agregar en Railway > Variables:
```
OPENAI_API_KEY=sk-...
```

### Buildpack

Railway detectará automáticamente `Aptfile` y instalará:
- `poppler-utils`
- `tesseract-ocr`
- `tesseract-ocr-spa`

### Verificar Deployment

1. Push a la rama `feature/pdf-jpeg-png-compatibility`
2. Railway rebuildeará automáticamente
3. Verificar logs:
   ```
   -----> Installing packages from Aptfile
          Fetching poppler-utils
          Fetching tesseract-ocr
   ```

## 📊 Precisión Esperada

| Método | Precisión | Velocidad |
|--------|-----------|-----------|
| Excel directo | 99.9% | Instantáneo |
| OCR + GPT-4 | 95-98% | ~5-15s por página |

**Factores que afectan precisión:**
- ✅ Calidad de imagen (300 DPI recomendado)
- ✅ Formato de tabla estructurado
- ❌ Imágenes borrosas o de baja resolución
- ❌ Layouts muy complejos o multi-columna

## 🔍 Troubleshooting

### Problema: "OPENAI_API_KEY not set"

**Solución**: Agregar variable de entorno en Railway o `.env` local.

### Problema: "pdf2image error"

**Solución**: Verificar que `poppler-utils` esté instalado:
```bash
# Test local
pdftoppm -v
```

### Problema: "pytesseract error"

**Solución**: Verificar instalación de tesseract:
```bash
# Test local
tesseract --version
```

### Problema: "No products extracted"

**Posibles causas:**
1. Imagen muy borrosa (OCR falló)
2. Formato no reconocido por GPT-4
3. PDF escaneado con mala calidad

**Solución**: Revisar logs para ver texto OCR extraído.

## 🎓 Mejoras Futuras (Opcional)

1. **Caché de OCR**: Guardar texto OCR para no repetir si se sube el mismo archivo
2. **UI Feedback**: Mostrar barra de progreso durante OCR+LLM
3. **Preview**: Mostrar preview del JSON antes de confirmar import
4. **Batch Processing**: Procesar múltiples PDFs en paralelo
5. **Fallback a GPT-4 Vision**: Si OCR falla, usar Vision API directamente

## 📝 Notas Importantes

- ⚠️ **Solo para Railway/Producción**: La API de OpenAI requiere conexión a internet
- ⚠️ **Costos variables**: Dependen del volumen de páginas procesadas
- ✅ **Idempotente**: Re-subir el mismo archivo actualizará precios existentes
- ✅ **Multi-proveedor**: Funciona igual que Excel (detecta proveedor del filename)

## ✅ Checklist de Merge

Antes de mergear a `main`:

- [x] Código implementado
- [x] Sin errores de linting
- [ ] Testeado localmente con PDF de ejemplo
- [ ] Testeado localmente con JPEG de ejemplo
- [ ] Variable `OPENAI_API_KEY` configurada en Railway
- [ ] Deployment a Railway exitoso
- [ ] Probado en Railway con archivo real
- [ ] Documentación completa

---

**Autor**: Implementado en rama `feature/pdf-jpeg-png-compatibility`  
**Fecha**: Octubre 2025

