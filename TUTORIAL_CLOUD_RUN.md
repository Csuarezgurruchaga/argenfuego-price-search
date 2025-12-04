# Tutorial Completo: Migración de Railway a Google Cloud Run

## 📚 Índice

1. [¿Qué es Google Cloud Run y por qué migrar?](#qué-es-google-cloud-run)
2. [Preparación del Proyecto](#preparación-del-proyecto)
3. [Configuración de Google Cloud](#configuración-de-google-cloud)
4. [Configuración de Base de Datos](#configuración-de-base-de-datos)
5. [Despliegue Paso a Paso](#despliegue-paso-a-paso)
6. [Troubleshooting Común](#troubleshooting-común)
7. [Comandos Útiles](#comandos-útiles)
8. [Mejores Prácticas](#mejores-prácticas)

---

## ¿Qué es Google Cloud Run?

### Conceptos Fundamentales

**Google Cloud Run** es un servicio **serverless** que ejecuta contenedores Docker. Esto significa:

- **No gestionas servidores**: Google se encarga de la infraestructura
- **Escala automáticamente**: De 0 a N instancias según el tráfico
- **Pago por uso**: Solo pagas cuando tu aplicación está procesando requests
- **HTTPS incluido**: Certificados SSL automáticos y gratuitos

### Comparación: Railway vs Cloud Run

| Característica | Railway | Cloud Run |
|---------------|---------|-----------|
| **Configuración** | `Procfile` o `nixpacks.toml` | `Dockerfile` (estándar de la industria) |
| **Base de datos** | Integrada en Railway | Externa (Cloud SQL, Supabase, etc.) |
| **Escalado** | Manual | Automático (0 a N instancias) |
| **Costo** | Plan fijo mensual | Pago por uso (tier gratuito generoso) |
| **Variables de entorno** | Panel web | CLI o Console + Secret Manager |
| **CI/CD** | Automático desde GitHub | Configurable con Cloud Build |

### Ventajas de Cloud Run

1. **Tier Gratuito Generoso**: 
   - 2 millones de requests/mes gratis
   - 360,000 GB-segundos de memoria gratis
   - 180,000 vCPU-segundos gratis

2. **Escalado a Cero**: 
   - Si no hay tráfico, no pagas nada
   - La primera request puede tardar unos segundos (cold start)

3. **Estándar de la Industria**: 
   - Usa Docker (conocimiento transferible)
   - Compatible con cualquier lenguaje/framework

---

## Preparación del Proyecto

### Paso 1: Crear el Dockerfile

El **Dockerfile** es la "receta" que define cómo construir tu aplicación en un contenedor Docker.

**¿Por qué necesitamos un Dockerfile?**
- Railway usa `nixpacks` que detecta automáticamente tu stack
- Cloud Run necesita un Dockerfile explícito (más control, más estándar)

#### Ejemplo de Dockerfile para FastAPI:

```dockerfile
# Usar imagen base oficial de Python
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
# (En nuestro caso: poppler-utils para PDFs, tesseract para OCR)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements y instalar dependencias de Python
# (Hacemos esto ANTES de copiar el código para aprovechar cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY app/ app/

# Exponer el puerto (Cloud Run usa la variable PORT automáticamente)
EXPOSE 8080

# Variable de entorno para el puerto
ENV PORT=8080

# Comando para ejecutar la aplicación
# Cloud Run establece $PORT automáticamente, nosotros lo usamos
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info
```

**Explicación línea por línea:**

1. `FROM python:3.11-slim`: Imagen base ligera con Python 3.11
2. `RUN apt-get...`: Instala herramientas del sistema necesarias
3. `WORKDIR /app`: Define el directorio de trabajo
4. `COPY requirements.txt .`: Copia el archivo de dependencias
5. `RUN pip install...`: Instala las dependencias de Python (se cachea si no cambia requirements.txt)
6. `COPY app/ app/`: Copia tu código de la aplicación
7. `EXPOSE 8080`: Documenta que el contenedor usa el puerto 8080
8. `ENV PORT=8080`: Define variable de entorno (Cloud Run la sobrescribe)
9. `CMD exec uvicorn...`: Comando que se ejecuta al iniciar el contenedor

**¿Por qué `--host 0.0.0.0`?**
- `0.0.0.0` significa "escuchar en todas las interfaces de red"
- Necesario para que Cloud Run pueda conectarse al contenedor

### Paso 2: Crear .dockerignore

El `.dockerignore` es como `.gitignore` pero para Docker. Excluye archivos innecesarios del build.

**¿Por qué es importante?**
- Reduce el tamaño de la imagen
- Acelera el build
- Evita copiar archivos sensibles (`.env`, etc.)

```dockerignore
# Python
__pycache__/
*.py[cod]
*.so
.venv/
venv/

# IDE
.vscode/
.idea/

# Git
.git/
.gitignore

# Testing
.pytest_cache/
.coverage

# Documentation (opcional, puedes incluir README.md)
*.md
!README.md

# Railway specific (ya no los necesitamos)
railway.toml
nixpacks.toml
Procfile

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

### Paso 3: Verificar que los Archivos Estáticos Estén en Git

**⚠️ Problema común**: Archivos estáticos (imágenes, CSS) ignorados por `.gitignore`

En nuestro caso, el logo estaba ignorado porque `.gitignore` tenía:
```
*.png
```

**Solución**: Permitir explícitamente los archivos estáticos de la app:

```gitignore
# Test files (local only)
*.png
test_*.py

# Pero sí versionamos el logo de la app
!app/static/logo.png
```

**¿Por qué es importante?**
- Cloud Run construye desde GitHub, no desde tu máquina local
- Si un archivo no está en Git, no estará en el contenedor

---

## Configuración de Google Cloud

### Paso 1: Instalar Google Cloud SDK

**En macOS:**
```bash
brew install google-cloud-sdk
```

**En Linux:**
```bash
# Descargar e instalar desde:
# https://cloud.google.com/sdk/docs/install
```

**Configurar PATH (agregar a `~/.zshrc` o `~/.bashrc`):**
```bash
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)
source /opt/homebrew/share/google-cloud-sdk/path.zsh.inc
source /opt/homebrew/share/google-cloud-sdk/completion.zsh.inc
```

### Paso 2: Autenticarse en Google Cloud

```bash
gcloud auth login
```

Esto abre tu navegador para autenticarte con tu cuenta de Google.

**¿Qué hace este comando?**
- Crea credenciales locales para usar la CLI de Google Cloud
- Te permite ejecutar comandos en nombre de tu cuenta

### Paso 3: Crear un Proyecto

Un **proyecto** en Google Cloud es como un "contenedor" que agrupa recursos relacionados.

```bash
# Crear proyecto
gcloud projects create argenfuego-quick-search \
    --name="ArgenFuego Quick Search"

# Seleccionar el proyecto como activo
gcloud config set project argenfuego-quick-search
```

**¿Por qué crear un proyecto separado?**
- Organización: Todos los recursos relacionados están juntos
- Facturación: Fácil ver cuánto gastas en este proyecto específico
- Permisos: Puedes dar acceso a otros solo a este proyecto

### Paso 4: Habilitar Facturación

**⚠️ Importante**: Cloud Run requiere facturación habilitada (aunque tengas tier gratuito)

**Opción 1: Desde la consola web**
1. Ve a: https://console.cloud.google.com/billing
2. Selecciona tu proyecto
3. Vincula una cuenta de facturación

**Opción 2: Desde la CLI**
```bash
# Listar cuentas de facturación disponibles
gcloud billing accounts list

# Vincular cuenta (reemplaza BILLING_ACCOUNT_ID)
gcloud billing projects link argenfuego-quick-search \
    --billing-account=BILLING_ACCOUNT_ID
```

**¿Por qué necesitas facturación?**
- Google requiere una tarjeta de crédito para prevenir abusos
- Con el tier gratuito, no te cobrarán a menos que superes los límites
- Tienes $300 de crédito gratis por 90 días

### Paso 5: Habilitar APIs Necesarias

Google Cloud organiza servicios en "APIs" que debes habilitar antes de usarlas.

```bash
# Cloud Run: Para ejecutar contenedores
gcloud services enable run.googleapis.com

# Cloud Build: Para construir imágenes Docker desde código
gcloud services enable cloudbuild.googleapis.com

# Cloud SQL Admin: Si vas a usar Cloud SQL (opcional)
gcloud services enable sqladmin.googleapis.com
```

**¿Por qué habilitar APIs?**
- Google Cloud usa un modelo de "opt-in" por seguridad
- Solo pagas por lo que usas
- Puedes ver qué APIs están habilitadas en la consola

### Paso 6: Configurar Región

```bash
# Configurar región por defecto para Cloud Run
gcloud config set run/region southamerica-east1
```

**¿Qué región elegir?**
- `southamerica-east1` (São Paulo): Más cercana a Argentina
- `us-central1`: Buena latencia, más barata
- `europe-west1`: Si tus usuarios están en Europa

**¿Por qué importa la región?**
- Latencia: Más cerca = más rápido
- Costos: Algunas regiones son más baratas
- Compliance: Algunos datos deben estar en ciertas regiones

---

## Configuración de Base de Datos

### Opción 1: Supabase (Recomendado para empezar)

**¿Por qué Supabase?**
- Plan gratuito generoso (500 MB de DB)
- PostgreSQL completo
- Fácil de configurar
- Incluye extras útiles (auth, storage)

#### Pasos:

1. **Crear cuenta en [supabase.com](https://supabase.com)**
   - Puedes usar GitHub para registro rápido

2. **Crear proyecto**:
   - Name: `argenfuego-quick-search`
   - Database Password: Crea una contraseña segura (¡guárdala!)
   - Region: `South America (São Paulo)`
   - Plan: `Free`

3. **Obtener URL de conexión**:
   - Settings → Database → Connection string
   - Copia la URL que aparece

4. **Convertir formato para tu app**:
   ```
   # URL de Supabase:
   postgresql://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres
   
   # URL para tu app (con psycopg):
   postgresql+psycopg://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres
   ```
   
   Solo cambia `postgresql://` por `postgresql+psycopg://`

### Opción 2: Cloud SQL (Más control, más costo)

```bash
# Crear instancia PostgreSQL
gcloud sql instances create argenfuego-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=southamerica-east1 \
    --root-password=TU_PASSWORD_SEGURO

# Crear base de datos
gcloud sql databases create argenfuego --instance=argenfuego-db
```

**Costo aproximado**: ~$7-10/mes para instancia pequeña

**Ventajas**:
- Más control sobre la configuración
- Integración nativa con Cloud Run
- Backups automáticos

---

## Despliegue Paso a Paso

### Método 1: Despliegue Directo desde Código Local

**Cuándo usar**: Para pruebas rápidas o cuando tienes cambios locales que aún no están en GitHub.

```bash
# Desde el directorio de tu proyecto
gcloud run deploy argenfuego-quick-search \
    --source . \
    --region southamerica-east1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=postgresql+psycopg://..." \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10
```

**¿Qué hace este comando?**
- `--source .`: Construye desde el directorio actual
- `--allow-unauthenticated`: Permite acceso público (sin autenticación)
- `--set-env-vars`: Define variables de entorno
- `--memory 1Gi`: Asigna 1 GB de RAM
- `--cpu 1`: Asigna 1 CPU
- `--timeout 300`: Timeout de 5 minutos por request
- `--max-instances 10`: Máximo 10 instancias simultáneas

### Método 2: Despliegue desde GitHub (Recomendado para Producción)

**Cuándo usar**: Cuando tu código está en GitHub y quieres despliegues reproducibles.

```bash
# Clonar repositorio en directorio temporal
cd /tmp
rm -rf argenfuego-price-search-temp
git clone https://github.com/TU_USUARIO/argenfuego-price-search.git argenfuego-price-search-temp
cd argenfuego-price-search-temp

# Desplegar desde el repo clonado
gcloud run deploy argenfuego-quick-search \
    --source . \
    --region southamerica-east1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=postgresql+psycopg://..." \
    --memory 1Gi \
    --cpu 1
```

**Ventajas**:
- Siempre despliegas la versión exacta que está en GitHub
- Reproducible: Cualquiera puede desplegar la misma versión
- Evita problemas con archivos locales no commiteados

### Método 3: CI/CD Automático con Cloud Build (Avanzado)

**Cuándo usar**: Cuando quieres despliegue automático en cada push a GitHub.

#### Paso 1: Crear `cloudbuild.yaml`

```yaml
steps:
  # Construir la imagen Docker
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:latest'
      - '.'

  # Subir la imagen a Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:$SHORT_SHA'

  # Desplegar en Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'argenfuego-quick-search'
      - '--image'
      - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:$SHORT_SHA'
      - '--region'
      - 'southamerica-east1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/argenfuego-quick-search:latest'
```

#### Paso 2: Crear Trigger de GitHub

```bash
# Conectar repositorio (primera vez)
gcloud builds triggers create github \
    --repo-name=argenfuego-price-search \
    --repo-owner=TU_USUARIO \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml \
    --name=deploy-cloud-run
```

**¿Qué hace esto?**
- Cada vez que haces `git push` a `main`, Cloud Build:
  1. Construye la imagen Docker
  2. La sube a Container Registry
  3. Despliega automáticamente en Cloud Run

---

## Variables de Entorno y Secrets

### Variables de Entorno Simples

```bash
# Agregar una variable
gcloud run services update argenfuego-quick-search \
    --update-env-vars "NUEVA_VAR=valor" \
    --region southamerica-east1

# Agregar múltiples variables
gcloud run services update argenfuego-quick-search \
    --update-env-vars "VAR1=valor1,VAR2=valor2" \
    --region southamerica-east1
```

### Secret Manager (Para Datos Sensibles)

**¿Por qué usar Secret Manager?**
- Las contraseñas no aparecen en logs
- Rotación fácil de secrets
- Auditoría de acceso

#### Crear un secreto:

```bash
# Crear secreto para DATABASE_URL
echo -n "postgresql+psycopg://postgres:password@host:5432/db" | \
    gcloud secrets create database-url --data-file=-

# Conceder permisos a Cloud Run
gcloud secrets add-iam-policy-binding database-url \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### Usar el secreto en Cloud Run:

```bash
gcloud run services update argenfuego-quick-search \
    --update-secrets DATABASE_URL=database-url:latest \
    --region southamerica-east1
```

**En tu código Python**, el secreto estará disponible como variable de entorno normal:
```python
import os
database_url = os.getenv("DATABASE_URL")
```

---

## Troubleshooting Común

### Problema 1: "Container failed to start"

**Síntomas**: El servicio no inicia, logs muestran errores.

**Soluciones**:
1. Verificar logs:
   ```bash
   gcloud run services logs read argenfuego-quick-search --limit=50
   ```

2. Verificar que `DATABASE_URL` esté correcta:
   - Formato: `postgresql+psycopg://user:pass@host:port/db`
   - Sin espacios extra
   - Contraseña codificada si tiene caracteres especiales

3. Verificar que el puerto sea `$PORT`:
   ```python
   # En tu código
   port = int(os.getenv("PORT", 8080))
   ```

### Problema 2: "404 Not Found" en archivos estáticos

**Síntomas**: CSS/JS/imágenes no cargan.

**Soluciones**:
1. Verificar que los archivos estén en Git:
   ```bash
   git ls-files app/static/
   ```

2. Verificar `.gitignore` no los ignore:
   ```bash
   git check-ignore app/static/logo.png
   ```

3. Verificar que el Dockerfile los copie:
   ```dockerfile
   COPY app/static/ app/static/
   ```

### Problema 3: "Connection timeout" a la base de datos

**Síntomas**: La app no puede conectar a PostgreSQL.

**Soluciones**:
1. Si usas Supabase:
   - Verificar que el proyecto esté completamente creado (puede tardar 2-5 min)
   - Verificar que la región sea correcta
   - Probar usar Connection Pooling en lugar de conexión directa

2. Si usas Cloud SQL:
   ```bash
   # Conectar Cloud Run a Cloud SQL
   gcloud run services update argenfuego-quick-search \
       --add-cloudsql-instances PROJECT_ID:REGION:INSTANCE_NAME \
       --region southamerica-east1
   ```

### Problema 4: Cold Start Lento

**Síntomas**: La primera request tarda mucho (10-30 segundos).

**Soluciones**:
1. Mantener al menos 1 instancia siempre activa:
   ```bash
   gcloud run services update argenfuego-quick-search \
       --min-instances=1 \
       --region southamerica-east1
   ```
   **Costo**: Pagas por la instancia incluso sin tráfico (~$5-10/mes)

2. Optimizar el Dockerfile:
   - Reducir tamaño de la imagen
   - Instalar menos dependencias
   - Usar imágenes base más pequeñas

### Problema 5: "Out of memory"

**Síntomas**: La aplicación se cae o funciona lento.

**Soluciones**:
1. Aumentar memoria:
   ```bash
   gcloud run services update argenfuego-quick-search \
       --memory 2Gi \
       --region southamerica-east1
   ```

2. Verificar uso de memoria en logs:
   ```bash
   gcloud run services logs read argenfuego-quick-search --limit=100 | grep -i memory
   ```

---

## Comandos Útiles

### Ver Información del Servicio

```bash
# Ver detalles completos
gcloud run services describe argenfuego-quick-search \
    --region southamerica-east1

# Ver solo la URL
gcloud run services describe argenfuego-quick-search \
    --region southamerica-east1 \
    --format="value(status.url)"
```

### Ver Logs

```bash
# Últimos 50 logs
gcloud run services logs read argenfuego-quick-search \
    --limit=50 \
    --region southamerica-east1

# Logs en tiempo real (seguimiento)
gcloud run services logs read argenfuego-quick-search \
    --follow \
    --region southamerica-east1

# Filtrar por nivel
gcloud run services logs read argenfuego-quick-search \
    --limit=100 \
    --region southamerica-east1 | grep ERROR
```

### Actualizar Configuración

```bash
# Actualizar memoria y CPU
gcloud run services update argenfuego-quick-search \
    --memory 2Gi \
    --cpu 2 \
    --region southamerica-east1

# Actualizar timeout
gcloud run services update argenfuego-quick-search \
    --timeout 600 \
    --region southamerica-east1

# Actualizar máximo de instancias
gcloud run services update argenfuego-quick-search \
    --max-instances 20 \
    --region southamerica-east1
```

### Listar y Eliminar Servicios

```bash
# Listar todos los servicios
gcloud run services list --region southamerica-east1

# Eliminar un servicio
gcloud run services delete argenfuego-quick-search \
    --region southamerica-east1
```

### Ver Métricas

```bash
# Ver métricas en la consola web
# https://console.cloud.google.com/run/detail/southamerica-east1/argenfuego-quick-search/metrics
```

---

## Mejores Prácticas

### 1. Siempre Desplegar desde GitHub

**❌ Mal:**
```bash
# Desplegar desde código local no commiteado
gcloud run deploy --source .
```

**✅ Bien:**
```bash
# Clonar repo y desplegar desde ahí
git clone https://github.com/user/repo.git
cd repo
gcloud run deploy --source .
```

**¿Por qué?**
- Reproducible: Cualquiera puede desplegar la misma versión
- Evita problemas con archivos locales
- Historial claro de qué versión está desplegada

### 2. Usar Secret Manager para Datos Sensibles

**❌ Mal:**
```bash
# Contraseña visible en comandos y logs
--set-env-vars "DATABASE_URL=postgresql://user:password123@host/db"
```

**✅ Bien:**
```bash
# Usar Secret Manager
gcloud secrets create database-url --data-file=-
gcloud run services update --update-secrets DATABASE_URL=database-url:latest
```

### 3. Configurar Límites Apropiados

**❌ Mal:**
```bash
# Sin límites (puede costar mucho si hay ataque)
--max-instances 1000
```

**✅ Bien:**
```bash
# Límite razonable según tu tráfico esperado
--max-instances 10
--memory 1Gi
--cpu 1
```

### 4. Monitorear Costos

```bash
# Ver facturación actual
# https://console.cloud.google.com/billing

# Configurar alertas de presupuesto
# https://console.cloud.google.com/billing/budgets
```

### 5. Usar Etiquetas para Organización

```bash
gcloud run services update argenfuego-quick-search \
    --update-labels environment=production,team=backend \
    --region southamerica-east1
```

### 6. Configurar Health Checks

Agrega un endpoint de health check en tu app:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

Luego configura en Cloud Run:
```bash
gcloud run services update argenfuego-quick-search \
    --health-check-path=/health \
    --region southamerica-east1
```

### 7. Usar Variables de Entorno para Configuración

**❌ Mal:**
```python
# Valores hardcodeados
DATABASE_URL = "postgresql://..."
```

**✅ Bien:**
```python
# Valores desde variables de entorno
import os
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

## Resumen del Flujo Completo

### Primera Vez (Setup Inicial)

1. ✅ Instalar Google Cloud SDK
2. ✅ `gcloud auth login`
3. ✅ Crear proyecto: `gcloud projects create ...`
4. ✅ Habilitar facturación
5. ✅ Habilitar APIs: `gcloud services enable ...`
6. ✅ Configurar región: `gcloud config set run/region ...`
7. ✅ Crear base de datos (Supabase o Cloud SQL)
8. ✅ Crear Dockerfile y .dockerignore
9. ✅ Asegurar que archivos estáticos estén en Git
10. ✅ Desplegar: `gcloud run deploy --source .`

### Despliegues Subsecuentes

1. ✅ Hacer cambios en código
2. ✅ Commit y push a GitHub
3. ✅ Clonar repo: `git clone ...`
4. ✅ Desplegar: `gcloud run deploy --source .`

### Con CI/CD (Avanzado)

1. ✅ Crear `cloudbuild.yaml`
2. ✅ Configurar trigger de GitHub
3. ✅ Cada `git push` despliega automáticamente

---

## Recursos Adicionales

- [Documentación oficial de Cloud Run](https://cloud.google.com/run/docs)
- [Precios de Cloud Run](https://cloud.google.com/run/pricing)
- [Mejores prácticas de Cloud Run](https://cloud.google.com/run/docs/tips)
- [Guía de Dockerfile](https://docs.docker.com/engine/reference/builder/)
- [Supabase Documentation](https://supabase.com/docs)

---

## Preguntas Frecuentes

### ¿Cuánto cuesta Cloud Run?

- **Tier gratuito**: 2M requests/mes, 360K GB-seg de memoria
- **Después**: ~$0.40 por millón de requests
- **Ejemplo**: 100K requests/mes = **Gratis**

### ¿Puedo usar mi dominio personalizado?

Sí, Cloud Run soporta dominios personalizados:
```bash
gcloud run domain-mappings create \
    --service argenfuego-quick-search \
    --domain tu-dominio.com \
    --region southamerica-east1
```

### ¿Cómo hago rollback a una versión anterior?

```bash
# Listar revisiones
gcloud run revisions list --service argenfuego-quick-search

# Hacer rollback a una revisión específica
gcloud run services update-traffic argenfuego-quick-search \
    --to-revisions REVISION_NAME=100 \
    --region southamerica-east1
```

### ¿Puedo ejecutar tareas programadas (cron jobs)?

Sí, usando Cloud Scheduler:
```bash
gcloud scheduler jobs create http my-job \
    --schedule="0 2 * * *" \
    --uri="https://tu-servicio.run.app/tarea" \
    --http-method=GET
```

---

¡Felicitaciones! 🎉 Ahora sabes cómo migrar de Railway a Cloud Run. Si tienes preguntas, consulta la documentación oficial o los logs de tu servicio.

