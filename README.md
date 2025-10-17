ArgenFuego Quick Search (FastAPI)
=================================

Aplicación web para subir Excel(es) de lista de precios, buscar productos con tolerancia a typos y calcular precio final aplicando un margen configurable.

Requisitos
----------

- Python 3.11+
- PostgreSQL (local o gestionado)
- (Prod) Railway con servicio PostgreSQL

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

Notas
-----

- Para grandes volúmenes, conviene optimizar la búsqueda con `pg_trgm` y/o limitar el pool de candidatos.
- Si tus Excel tienen encabezados distintos, podés editar el mapeo en `app/services/importer.py`.

