# Guía de Migración: Railway → Google Cloud Run

## ¿Qué es Google Cloud Run?

**Google Cloud Run** es un servicio serverless completamente gestionado que permite ejecutar contenedores Docker de forma escalable y sin necesidad de gestionar servidores. Algunas características clave:

- **Serverless**: No necesitas gestionar servidores, escalado automático
- **Pago por uso**: Solo pagas por el tiempo que tu aplicación está procesando requests
- **Escalado a cero**: Si no hay tráfico, no se ejecutan instancias (ahorro de costos)
- **Escalado automático**: Se adapta automáticamente al tráfico
- **HTTPS incluido**: Certificados SSL automáticos
- **Integración con GitHub**: Puedes configurar CI/CD automático

### Diferencias principales con Railway:

| Característica | Railway | Cloud Run |
|---------------|---------|----------|
| Configuración | `Procfile` / `nixpacks.toml` | `Dockerfile` |
| Base de datos | Integrada en Railway | Cloud SQL (PostgreSQL) o externa |
| Variables de entorno | Panel web | Cloud Run Console o Secret Manager |
| Escalado | Manual | Automático |
| Costos | Plan fijo | Pago por uso |

---

## Requisitos Previos

1. **Cuenta de Google Cloud Platform (GCP)**
   - Crea una cuenta en [cloud.google.com](https://cloud.google.com)
   - Activa el período de prueba gratuito ($300 de crédito por 90 días)

2. **Google Cloud SDK (gcloud CLI)**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # O descarga desde: https://cloud.google.com/sdk/docs/install
   ```

3. **Docker** (opcional, para pruebas locales)
   ```bash
   # macOS
   brew install docker
   ```

4. **Repositorio en GitHub** (ya lo tienes)

---

## Paso 1: Configurar Google Cloud

### 1.1. Iniciar sesión y crear proyecto

```bash
# Iniciar sesión en Google Cloud
gcloud auth login

# Crear un nuevo proyecto (o usar uno existente)
gcloud projects create argenfuego-quick-search --name="ArgenFuego Quick Search"

# Seleccionar el proyecto
gcloud config set project argenfuego-quick-search

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com  # Si usas Cloud SQL
```

### 1.2. Configurar autenticación

```bash
# Configurar Docker para usar gcloud como helper
gcloud auth configure-docker

# Establecer región (ej: us-central1, southamerica-east1 para Argentina)
gcloud config set run/region southamerica-east1
```

---

## Paso 2: Configurar Base de Datos PostgreSQL

Tienes dos opciones:

### Opción A: Cloud SQL (PostgreSQL gestionado) - Recomendado

```bash
# Crear instancia de Cloud SQL PostgreSQL
gcloud sql instances create argenfuego-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=southamerica-east1 \
    --root-password=TU_PASSWORD_SEGURO

# Crear base de datos
gcloud sql databases create argenfuego --instance=argenfuego-db

# Obtener la IP pública (si necesitas acceso externo)
gcloud sql instances describe argenfuego-db --format="value(ipAddresses[0].ipAddress)"
```

**Nota**: Cloud SQL puede ser costoso. Considera usar una instancia pequeña (`db-f1-micro`) para desarrollo.

### Opción B: Base de datos externa (Railway, Supabase, etc.)

Si ya tienes PostgreSQL en Railway u otro servicio, puedes seguir usándolo. Solo necesitarás la URL de conexión.

---

## Paso 3: Preparar el Código

Los archivos necesarios ya están creados:
- ✅ `Dockerfile` - Define cómo construir la imagen
- ✅ `.dockerignore` - Excluye archivos innecesarios del build

### Verificar que todo esté correcto:

```bash
# Probar el Dockerfile localmente (opcional)
docker build -t argenfuego-test .
docker run -p 8080:8080 -e DATABASE_URL="tu_url_aqui" argenfuego-test
```

---

## Paso 4: Desplegar en Cloud Run

### Método 1: Desde la línea de comandos (Recomendado para primera vez)

```bash
# Construir y desplegar en un solo comando
gcloud run deploy argenfuego-quick-search \
    --source . \
    --platform managed \
    --region southamerica-east1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname" \
    --set-env-vars "DEFAULT_MARGIN=1.5" \
    --set-env-vars "ROUNDING_STRATEGY=nearest_10" \
    --set-env-vars "DEFAULT_IVA=1.21" \
    --set-env-vars "DEFAULT_IIBB=1.025" \
    --set-env-vars "DEFAULT_PROFIT=1.0" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10
```

**Variables de entorno importantes:**
- `DATABASE_URL`: URL completa de PostgreSQL
- `DEFAULT_MARGIN`: Margen por defecto (ej: 1.5)
- `ROUNDING_STRATEGY`: Estrategia de redondeo
- `OPENAI_API_KEY`: (Opcional) Para funciones OCR/LLM

### Método 2: Desde Google Cloud Console (Interfaz Web)

1. Ve a [Cloud Run Console](https://console.cloud.google.com/run)
2. Click en "CREATE SERVICE"
3. Selecciona "Deploy one revision from a source repository" o "Deploy a container image"
4. Si usas GitHub:
   - Conecta tu repositorio
   - Selecciona la rama (ej: `main` o `feature/new-work`)
   - Cloud Build construirá automáticamente la imagen
5. Configura:
   - **Service name**: `argenfuego-quick-search`
   - **Region**: `southamerica-east1` (o la que prefieras)
   - **Authentication**: Allow unauthenticated invocations (si quieres acceso público)
   - **Memory**: 1 GiB (o más si procesas muchos PDFs)
   - **CPU**: 1
   - **Timeout**: 300 segundos
   - **Max instances**: 10 (ajusta según necesidad)
6. En "Variables and Secrets", agrega todas las variables de entorno
7. Click "CREATE"

---

## Paso 5: Configurar Variables de Entorno y Secrets

### Usando Google Secret Manager (Recomendado para datos sensibles)

```bash
# Crear secretos para información sensible
echo -n "tu_password_db" | gcloud secrets create database-password --data-file=-

# Crear secreto para DATABASE_URL completa
echo -n "postgresql+psycopg://user:pass@host:5432/db" | gcloud secrets create database-url --data-file=-

# Conceder permisos a Cloud Run
gcloud secrets add-iam-policy-binding database-url \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

Luego, en Cloud Run Console, agrega las variables usando Secret Manager:
- Variable: `DATABASE_URL`
- Value: Selecciona "Reference a secret" → `database-url`

### Variables de entorno directas (menos seguras)

Puedes agregarlas directamente en Cloud Run Console o vía CLI:

```bash
gcloud run services update argenfuego-quick-search \
    --update-env-vars "DEFAULT_MARGIN=1.5,ROUNDING_STRATEGY=nearest_10"
```

---

## Paso 6: Configurar Cloud SQL Connection (Si usas Cloud SQL)

Si tu base de datos está en Cloud SQL, necesitas configurar la conexión:

```bash
# Conectar Cloud Run a Cloud SQL
gcloud run services update argenfuego-quick-search \
    --add-cloudsql-instances argenfuego-db \
    --set-env-vars "INSTANCE_CONNECTION_NAME=PROJECT_ID:southamerica-east1:argenfuego-db"
```

Luego, actualiza tu `DATABASE_URL` para usar el socket de Cloud SQL:
```
postgresql+psycopg://user:password@/dbname?host=/cloudsql/PROJECT_ID:southamerica-east1:argenfuego-db
```

---

## Paso 7: Configurar CI/CD con GitHub (Opcional pero Recomendado)

### 7.1. Crear Cloud Build Trigger

```bash
# Conectar repositorio de GitHub
gcloud builds triggers create github \
    --repo-name=argenfuego-quick-search \
    --repo-owner=TU_USUARIO_GITHUB \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml \
    --name=deploy-cloud-run
```

### 7.2. Crear archivo `cloudbuild.yaml`

Ya está creado en el repositorio. Este archivo define cómo Cloud Build construye y despliega tu aplicación automáticamente cuando haces push a GitHub.

---

## Paso 8: Verificar el Despliegue

```bash
# Obtener la URL de tu servicio
gcloud run services describe argenfuego-quick-search --format="value(status.url)"

# Probar el endpoint
curl https://TU_URL.run.app/
```

---

## Paso 9: Monitoreo y Logs

### Ver logs en tiempo real:

```bash
gcloud run services logs read argenfuego-quick-search --follow
```

### En Cloud Console:

1. Ve a Cloud Run → Tu servicio → "LOGS"
2. Puedes filtrar por nivel, tiempo, etc.

---

## Paso 10: Migrar Datos (Si es necesario)

Si necesitas migrar datos desde Railway a Cloud SQL:

```bash
# Exportar desde Railway (si tienes acceso SSH)
pg_dump $RAILWAY_DATABASE_URL > backup.sql

# Importar a Cloud SQL
gcloud sql import sql argenfuego-db gs://BUCKET_NAME/backup.sql --database=argenfuego
```

O usa herramientas como `pg_dump` y `psql` directamente.

---

## Costos Estimados

### Cloud Run:
- **Gratis**: Primeros 2 millones de requests/mes
- **Después**: ~$0.40 por millón de requests
- **CPU/Memoria**: ~$0.00002400 por GB-segundo
- **Tiempo de ejecución**: ~$0.00000250 por 100ms

### Cloud SQL (si lo usas):
- **db-f1-micro**: ~$7-10/mes
- **db-g1-small**: ~$25-30/mes

**Ejemplo mensual para tráfico moderado:**
- 100,000 requests/mes: **Gratis** (dentro del tier gratuito)
- Base de datos pequeña: ~$7-10/mes
- **Total estimado**: ~$7-10/mes (vs Railway que puede ser $5-20/mes)

---

## Troubleshooting

### Error: "Container failed to start"

- Verifica los logs: `gcloud run services logs read argenfuego-quick-search`
- Asegúrate de que `DATABASE_URL` esté correctamente configurada
- Verifica que el puerto sea `$PORT` (Cloud Run lo establece automáticamente)

### Error: "Connection refused" a la base de datos

- Si usas Cloud SQL, verifica que Cloud Run tenga permisos
- Si usas base de datos externa, verifica firewall/whitelist de IPs
- Cloud Run tiene IPs dinámicas, considera usar Private IP o Cloud SQL Auth Proxy

### La aplicación es lenta al iniciar

- Cloud Run puede escalar a cero, la primera request puede tardar (cold start)
- Considera aumentar `--min-instances=1` para evitar cold starts:
  ```bash
  gcloud run services update argenfuego-quick-search --min-instances=1
  ```

### Problemas con dependencias del sistema (tesseract, poppler)

- Verifica que el Dockerfile incluya todas las dependencias
- Reconstruye la imagen: `gcloud run deploy --source .`

---

## Comandos Útiles

```bash
# Listar servicios
gcloud run services list

# Ver detalles de un servicio
gcloud run services describe argenfuego-quick-search

# Actualizar variables de entorno
gcloud run services update argenfuego-quick-search \
    --update-env-vars "NUEVA_VAR=valor"

# Ver logs
gcloud run services logs read argenfuego-quick-search --limit=50

# Redesplegar después de cambios
gcloud run deploy argenfuego-quick-search --source .

# Eliminar servicio
gcloud run services delete argenfuego-quick-search
```

---

## Próximos Pasos

1. ✅ Desplegar en Cloud Run
2. ✅ Configurar dominio personalizado (opcional)
3. ✅ Configurar alertas y monitoreo
4. ✅ Configurar backup automático de base de datos
5. ✅ Optimizar costos (ajustar recursos según uso real)

---

## Recursos Adicionales

- [Documentación oficial de Cloud Run](https://cloud.google.com/run/docs)
- [Precios de Cloud Run](https://cloud.google.com/run/pricing)
- [Guía de migración de Railway a Cloud Run](https://cloud.google.com/run/docs/migrating)
- [Mejores prácticas de Cloud Run](https://cloud.google.com/run/docs/tips)

---

¡Buena suerte con la migración! 🚀

