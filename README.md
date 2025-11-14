ArgenFuego Quick Search (FastAPI)
=================================

Aplicación web para subir Excel(es) de lista de precios, buscar productos con tolerancia a typos y calcular precio final aplicando un margen configurable.

Requisitos
----------

- Python 3.11+
- PostgreSQL (local o gestionado)
- (Prod) Railway con servicio PostgreSQL o Google Cloud Run + Cloud SQL

Instalación local
-----------------

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Usar una cadena válida de Postgres (Docker, local, Railway, etc.)
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/argenfuego
export DEFAULT_MARGIN=1.5
uvicorn app.main:app --reload
```

Abrí `http://localhost:8000`.

Configuración
-------------

Variables de entorno:

- `DATABASE_URL`: URL a Postgres (obligatoria). Ej: `postgresql+psycopg://user:pass@host:port/db`.
- `DEFAULT_MARGIN`: Margen por defecto (1.5 = 50%).
- `ROUNDING_STRATEGY`: `none` | `nearest_10` | `ceil_10` | `floor_10`.
- `DEFAULT_IVA`: Multiplicador de IVA (por defecto: 1.21).
- `DEFAULT_IIBB`: Multiplicador de IIBB (por defecto: 1.025).
- `DEFAULT_PROFIT`: Multiplicador de ganancia (por defecto: 1.0).
- `OPENAI_API_KEY`: (Opcional) Para funciones OCR/LLM de procesamiento de PDFs.

Flujo
-----

- Página principal: buscar por nombre/palabra clave; ajustar margen.
- Subir Excel(s): se parsean hojas automáticamente, detectando columnas (producto, precio, sku, moneda) heurísticamente.
- Ajustes: definir margen por defecto y redondeo.

Deploy en Railway
-----------------

1. Crear nuevo proyecto y servicio de `PostgreSQL`.
2. Crear nuevo servicio `Web` desde este repo.
3. Variables:
   - `DATABASE_URL`: usar la de Postgres.
   - `DEFAULT_MARGIN`: ej `1.5`.
   - `ROUNDING_STRATEGY`: ej `nearest_10`.
4. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway detecta `requirements.txt` y construye con Nixpacks. No hace falta Dockerfile.

Deploy en Google Cloud Run
---------------------------

Ver la guía completa de migración en [`MIGRACION_CLOUD_RUN.md`](MIGRACION_CLOUD_RUN.md).

**Resumen rápido:**

1. Instalar Google Cloud SDK y autenticarse:
   ```bash
   gcloud auth login
   gcloud config set project TU_PROJECT_ID
   ```

2. Desplegar desde el código fuente:
   ```bash
   gcloud run deploy argenfuego-quick-search \
       --source . \
       --region southamerica-east1 \
       --allow-unauthenticated \
       --set-env-vars "DATABASE_URL=postgresql+psycopg://..." \
       --memory 1Gi \
       --cpu 1
   ```

3. Configurar variables de entorno en Cloud Run Console o vía CLI.

**Archivos necesarios:**
- `Dockerfile`: Define la imagen Docker con todas las dependencias
- `.dockerignore`: Excluye archivos innecesarios del build
- `cloudbuild.yaml`: (Opcional) Para CI/CD automático desde GitHub

**Notas importantes:**
- Cloud Run usa la variable `PORT` automáticamente (no necesitas configurarla)
- Para bases de datos Cloud SQL, configura la conexión con `--add-cloudsql-instances`
- Considera usar Secret Manager para datos sensibles como `DATABASE_URL`

Notas
-----

- Para grandes volúmenes, conviene optimizar la búsqueda con `pg_trgm` y/o limitar el pool de candidatos.
- Si tus Excel tienen encabezados distintos, podés editar el mapeo en `app/services/importer.py`.
- Cloud Run escala automáticamente y puede escalar a cero cuando no hay tráfico (ahorro de costos).

