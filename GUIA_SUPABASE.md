# Guía: Configurar Supabase para ArgenFuego Quick Search

## Paso 1: Crear cuenta en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Click en **"Start your project"** o **"Sign Up"**
3. Puedes registrarte con:
   - GitHub (recomendado, más rápido)
   - Email
   - Google

## Paso 2: Crear un nuevo proyecto

1. Una vez dentro del dashboard, click en **"New Project"**
2. Completa el formulario:
   - **Name**: `argenfuego-quick-search` (o el nombre que prefieras)
   - **Database Password**: Crea una contraseña segura (¡guárdala!)
   - **Region**: Elige la más cercana:
     - `South America (São Paulo)` - Mejor para Argentina
     - `US East (North Virginia)` - Alternativa
   - **Pricing Plan**: Selecciona **"Free"** (tier gratuito)
3. Click en **"Create new project"**
4. Espera 2-3 minutos mientras se crea el proyecto

## Paso 3: Obtener la URL de conexión

Una vez que el proyecto esté listo:

1. En el dashboard, ve a **Settings** (⚙️) en el menú lateral
2. Click en **Database**
3. Busca la sección **"Connection string"** o **"Connection pooling"**
4. Selecciona **"URI"** o **"Connection string"**
5. Copia la URL que se ve así:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

### ⚠️ Importante: Formato para tu aplicación

Tu aplicación usa `psycopg` como driver, así que necesitas convertir la URL:

**URL de Supabase:**
```
postgresql://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

**URL para tu aplicación (con psycopg):**
```
postgresql+psycopg://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

O simplemente reemplaza `postgresql://` por `postgresql+psycopg://` en la URL que copiaste.

## Paso 4: Configurar la conexión (Opcional - Pooling)

Para mejor rendimiento en producción, Supabase recomienda usar **Connection Pooling**:

1. En Settings → Database, busca **"Connection pooling"**
2. Usa el modo **"Transaction"** (recomendado para aplicaciones web)
3. La URL será diferente, algo como:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-southamerica-east1.pooler.supabase.com:6543/postgres
   ```
4. Convierte a formato psycopg:
   ```
   postgresql+psycopg://postgres.xxxxx:TU_PASSWORD@aws-0-southamerica-east1.pooler.supabase.com:6543/postgres
   ```

## Paso 5: Probar la conexión localmente (Opcional)

Antes de desplegar en Cloud Run, puedes probar la conexión localmente:

```bash
# En tu proyecto local
export DATABASE_URL="postgresql+psycopg://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
export DEFAULT_MARGIN=1.5

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

Si todo funciona, la aplicación creará las tablas automáticamente al iniciar.

## Paso 6: Configurar variables de entorno en Cloud Run

Cuando despliegues en Cloud Run, usa esta URL como variable de entorno:

```bash
gcloud run deploy argenfuego-quick-search \
    --source . \
    --region southamerica-east1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=postgresql+psycopg://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres" \
    --set-env-vars "DEFAULT_MARGIN=1.5" \
    --set-env-vars "ROUNDING_STRATEGY=nearest_10" \
    --memory 1Gi \
    --cpu 1
```

## Paso 7: Migrar datos existentes (Si aplica)

Si ya tienes datos en Railway u otra base de datos:

### Exportar desde Railway:
```bash
# Si tienes acceso SSH a Railway
pg_dump $RAILWAY_DATABASE_URL > backup.sql
```

### Importar a Supabase:
1. En Supabase Dashboard → **SQL Editor**
2. Click en **"New query"**
3. O usa `psql` desde tu terminal:
   ```bash
   psql "postgresql://postgres:TU_PASSWORD@db.xxxxx.supabase.co:5432/postgres" < backup.sql
   ```

## Configuración de seguridad

### Restricción de IPs (Opcional pero recomendado)

Por defecto, Supabase permite conexiones desde cualquier IP. Para mayor seguridad:

1. Ve a Settings → Database
2. Busca **"Connection pooling"** → **"Allowed IP addresses"**
3. Agrega las IPs de Cloud Run (puedes usar `0.0.0.0/0` temporalmente, pero no es lo más seguro)

**Nota**: Cloud Run tiene IPs dinámicas, así que es difícil restringir por IP. Una alternativa es usar **Connection Pooling** que es más seguro.

## Límites del plan gratuito de Supabase

- ✅ **500 MB** de base de datos
- ✅ **2 GB** de almacenamiento de archivos
- ✅ **2 GB** de transferencia de datos/mes
- ✅ Sin límite de tiempo (permanente)
- ✅ Hasta **500 MB** de base de datos
- ⚠️ Si superas los límites, te pedirán actualizar al plan Pro ($25/mes)

## Troubleshooting

### Error: "password authentication failed"
- Verifica que la contraseña sea correcta
- Asegúrate de usar la URL correcta (con o sin pooling)

### Error: "connection timeout"
- Verifica que la región de Supabase sea la correcta
- Intenta usar Connection Pooling en lugar de conexión directa

### Error: "too many connections"
- Usa Connection Pooling (modo Transaction)
- Limita el número de conexiones en tu aplicación

### La aplicación no crea las tablas
- Verifica que la URL de conexión sea correcta
- Revisa los logs de Cloud Run: `gcloud run services logs read argenfuego-quick-search`
- Asegúrate de que el formato de la URL incluya `postgresql+psycopg://`

## Próximos pasos

Una vez que tengas la URL de Supabase:

1. ✅ Prueba la conexión localmente (opcional)
2. ✅ Despliega en Cloud Run con la URL de Supabase
3. ✅ Verifica que la aplicación funcione correctamente
4. ✅ Migra datos si es necesario

---

**¿Necesitas ayuda con algún paso específico?** Puedo ayudarte a configurar la conexión o resolver cualquier problema que encuentres.

