# Guía de Despliegue de GestVet en Producción

Esta guía contiene los pasos detallados para desplegar la arquitectura completa de **GestVet**: Base de Datos PostgreSQL (Supabase), Almacenamiento de Adjuntos (Supabase Storage), API Backend (FastAPI en Render Free), SPA Frontend (React + Vite en Vercel) y Cron de Recordatorios (GitHub Actions).

---

## 1. Estrategia de Regiones y Latencia

> [!IMPORTANT]
> **Coincidencia de Regiones:** Para evitar retardos en las consultas médicas y de citas, es **indispensable** seleccionar la misma región de centro de datos para el Backend y la Base de Datos.
> - **Región Recomendada:** `us-east-1` (N. Virginia) en Supabase, Render y Vercel.
> - La latencia directa entre Backend y BD debe mantenerse en **<10 ms**.

---

## 2. Paso 1: Base de Datos y Storage en Supabase

Recomendado: **Supabase** (PostgreSQL administrado + Object Storage S3-compatible).

### 2.1 Conexión a la Base de Datos PostgreSQL
1. Crea un nuevo proyecto en Supabase en la región **US East (N. Virginia)**.
2. Dirígete a **Project Settings → Database → Connection string**.
3. Selecciona el modo **Session pooler** (puerto `5432`):
   - **NO** uses la conexión "Direct" (puerto 5432 sin pooler): en Supabase resuelve solo a direcciones IPv6 y Render no garantiza salida IPv6 en su red.
   - **NO** uses el "Transaction pooler" (puerto 6543): este modo no soporta prepared statements y rompe con `asyncpg` (`prepared statement already exists`).
4. Copia la cadena del Session Pooler y cambia el prefijo `postgresql://` por `postgresql+asyncpg://`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres.[ref-proyecto]:[tu-password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```

### 2.2 Creación del Bucket de Adjuntos (Supabase Storage)
Dado que el backend corre en el plan Free de Render (sin disco persistente), los adjuntos (radiografías, análisis clínicos y evidencias del Libro de Reclamaciones) se guardan en Supabase Storage:
1. En el Dashboard de Supabase, ingresa a **Storage**.
2. Haz clic en **New bucket**.
3. Nombre del bucket: `attachments`.
4. **Deja desmarcada** la opción **Public bucket**: el bucket debe ser **privado**. Los adjuntos son datos clínicos y evidencia de reclamos; con un bucket público cualquiera que tenga el enlace puede verlos.
5. Subir, leer y borrar lo hace solo el backend, autenticado con `SUPABASE_SERVICE_ROLE_KEY` (con bypass de RLS). El navegador nunca pide el archivo a Supabase: lo pide a la API (`/api/v1/medical-records/attachments/{id}/file` y `/api/v1/complaints/evidence/{id}/file`), que comprueba quién lo pide antes de entregarlo. No hace falta ninguna política de RLS.

> **Si el bucket ya existía como público** (despliegues anteriores a este cambio): en el Dashboard de Supabase, **Storage → `attachments` → Edit bucket**, desmarca **Public bucket** y guarda. Es un paso manual; ningún despliegue lo hace solo. Los archivos ya subidos siguen funcionando, porque la API los lee con la clave de servicio.

---

## 3. Paso 2: Despliegue del Backend en Render (Plan Free)

El backend corre en un **Web Service** de Render usando Python 3.13 y `uv`. Puede desplegarse mediante el archivo [`render.yaml`](render.yaml) (Blueprint) o manualmente:

### Configuración en Render:
- **Environment:** Python 3.13
- **Root Directory:** `backend`
- **Build Command:**
  ```bash
  pip install uv && uv sync --frozen --no-dev && uv run alembic upgrade head
  ```
- **Start Command:**
  ```bash
  uv run uvicorn gestvet.main:app --app-dir src --host 0.0.0.0 --port $PORT
  ```
- **Region:** Virginia (US East)
- **Plan:** Free

### Variables de Entorno del Backend:
```env
APP_NAME=gestvet-api
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO
LOG_JSON=true

# Conexión a la BD (Session Pooler de Supabase en puerto 5432)
DATABASE_URL=postgresql+asyncpg://postgres.[ref-proyecto]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Orígenes autorizados por CORS y URLs base
CORS_ALLOWED_ORIGINS=["https://gestvet-pi.vercel.app"]
FRONTEND_BASE_URL=https://gestvet-pi.vercel.app

# Almacenamiento persistente en Supabase Storage (bucket PRIVADO)
SUPABASE_URL=https://[ref-proyecto].supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_secret_key_de_supabase
SUPABASE_STORAGE_BUCKET=attachments

# Ruta local de adjuntos (fallback para desarrollo local)
ATTACHMENTS_STORAGE_DIR=./var/attachments

# Clave secreta JWT (generar con python -c "import secrets; print(secrets.token_urlsafe(48))")
JWT_SECRET_KEY=tu_clave_secreta_jwt_de_al_menos_32_caracteres_super_segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_SECONDS=3600

# Token secreto para el Cron de Recordatorios de WhatsApp (GitHub Actions)
REMINDERS_CRON_TOKEN=tu_token_secreto_para_el_cron_de_recordatorios

# Confirmación simulada del cobro por QR: siempre apagada en producción
QR_SIMULATION_ENABLED=false

# Integración con IA (OpenRouter)
OPENROUTER_API_KEY=tu_openrouter_api_key_aqui
OPENROUTER_MODEL=deepseek/deepseek-v4.1-flash
OPENROUTER_FALLBACK_MODEL=deepseek/deepseek-v4-flash-0731
OPENROUTER_TIMEOUT_SECONDS=45

# Verificación DNI Factiliza (opcional)
FACTILIZA_API_KEY=tu_factiliza_key
```

---

## 4. Paso 3: Cron de Recordatorios de WhatsApp (GitHub Actions)

En el plan Free de Render, el contenedor entra en reposo tras 15 minutos sin tráfico HTTP, lo que detiene los bucles en segundo plano. Para garantizar el envío puntual de recordatorios de citas (24h antes) y vacunas por vencer:

1. El repositorio incluye el flujo [`.github/workflows/reminders-cron.yml`](.github/workflows/reminders-cron.yml), configurado para ejecutarse cada 30 minutos de lunes a viernes (hora de Lima; sábados y domingos no corre) y manualmente vía `workflow_dispatch`.
2. En GitHub, ve a **Settings → Secrets and variables → Actions** y añade los siguientes **Repository Secrets**:
   - `API_BASE_URL`: `https://gestvet-api.onrender.com`
   - `REMINDERS_CRON_TOKEN`: El mismo token secreto configurado en la variable `REMINDERS_CRON_TOKEN` de Render.
3. El workflow realiza peticiones `curl` con reintentos y tiempo de espera de 90 segundos para permitir el arranque en frío de Render.

---

## 5. Paso 4: Despliegue del Frontend (React + Vite en Vercel)

Recomendado: **Vercel**.

### Configuración en Vercel:
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `pnpm build` (o `npm run build`)
- **Output Directory:** `dist`

### Variables de Entorno del Frontend:
```env
VITE_API_BASE_URL=https://gestvet-api.onrender.com
```

---

## 6. Accesibilidad (Sienna)

El widget de accesibilidad es [Sienna](https://github.com/bennyluk/Sienna-Accessibility-Widget) (MIT, código abierto), instalado como dependencia npm del frontend (`sienna-accessibility`). Se auto-inicializa al cargar la app sin necesidad de cuenta propia ni API key; **sí descarga los archivos de idioma (locale) y fuentes tipográficas desde `cdn.jsdelivr.net`** en tiempo de ejecución. Reemplazó a UserWay.

---

## 7. Lista de Comprobación Final (Checklist)

- [x] Favicons oficiales (`favicon.ico`, `favicon.png`, `gestvet-icon.png`) cargados en la pestaña.
- [x] Isotipo oficial (huella con corazón calado en degradado azul/cian) renderizado en la cabecera.
- [x] Aceptación obligatoria de **Términos y Condiciones** requerida en el registro.
- [x] Asistente de IA (OpenRouter) configurado con fallback automático.
- [ ] Base de datos PostgreSQL configurada en Supabase con Session Pooler (puerto 5432).
- [ ] Bucket **privado** `attachments` creado en Supabase Storage (o el existente pasado a privado).
- [ ] Migraciones de base de datos aplicadas en el despliegue de Render (`uv run alembic upgrade head`).
- [ ] Secretos `API_BASE_URL` y `REMINDERS_CRON_TOKEN` configurados en GitHub Actions.
