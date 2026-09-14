# Guía de Despliegue de GestVet en Producción

Esta guía contiene los pasos detallados para desplegar la arquitectura completa de **GestVet**: Base de Datos PostgreSQL, API Backend (FastAPI) y SPA Frontend (React + Vite).

---

## 1. Estrategia de Regiones y Latencia

> [!IMPORTANT]
> **Coincidencia de Regiones:** Para evitar retardos en las consultas médicas y de citas, es **indispensable** seleccionar la misma región de centro de datos para el Backend y la Base de Datos.
> - **Región Recomendada:** `us-east-1` (N. Virginia) en AWS / Render / Supabase / Vercel (o `sa-east-1` São Paulo si la plataforma lo soporta).
> - La latencia directa entre Backend y BD debe mantenerse en **<10 ms**.

---

## 2. Paso 1: Base de Datos PostgreSQL

Puedes usar un servicio gestionado como **Supabase**, **Neon.tech** o **Render PostgreSQL**.

1. Crea un nuevo proyecto PostgreSQL.
2. Selecciona la región **US East (N. Virginia)**.
3. Copia la cadena de conexión en formato `postgresql+asyncpg://`:
   ```env
   DATABASE_URL=postgresql+asyncpg://usuario:password@host:5432/gestvet
   ```

---

## 3. Paso 2: Despliegue del Backend (FastAPI)

Recomendado: **Render.com** (Web Service), **Railway.app** o **Fly.io**.

### Configuración en Render / Railway:
- **Environment:** Python 3.13
- **Build Command:** `pip install uv && uv pip install --system -r pyproject.toml` (o `pip install .`)
- **Start Command:** `uvicorn gestvet.main:app --host 0.0.0.0 --port $PORT`
- **Region:** US East (N. Virginia)

### Variables de Entorno del Backend:
```env
APP_NAME=gestvet-api
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO
LOG_JSON=true

# Conexión a la BD
DATABASE_URL=postgresql+asyncpg://usuario:password@host:5432/gestvet

# Orígenes autorizados por CORS (tu URL de frontend en Vercel)
CORS_ALLOWED_ORIGINS=["https://gestvet.vercel.app","https://tu-dominio.com"]
FRONTEND_BASE_URL=https://gestvet.vercel.app
API_BASE_URL=https://gestvet-api.onrender.com

# Clave secreta JWT (generar con python -c "import secrets; print(secrets.token_urlsafe(48))")
JWT_SECRET_KEY=tu_clave_secreta_jwt_de_al_menos_32_caracteres_super_segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_SECONDS=3600

# Integración con IA (OpenRouter)
OPENROUTER_API_KEY=tu_openrouter_api_key_aqui
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_FALLBACK_MODEL=google/gemini-2.5-flash
OPENROUTER_TIMEOUT_SECONDS=45

# Verificación DNI Factiliza (opcional)
FACTILIZA_API_KEY=tu_factiliza_key
```

### Ejecutar Migraciones en Producción:
Una vez conectada la base de datos, ejecuta las migraciones de Alembic desde tu terminal o script de inicio:
```bash
alembic upgrade head
```

---

## 4. Paso 3: Despliegue del Frontend (React + Vite)

Recomendado: **Vercel** o **Netlify**.

### Configuración en Vercel:
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Root Directory:** `frontend`

### Variables de Entorno del Frontend:
```env
VITE_API_BASE_URL=https://gestvet-api.onrender.com
VITE_USERWAY_ACCOUNT_ID=tu_userway_account_id
```

---

## 5. Configuración de Accesibilidad (UserWay)

1. Ingresa a [UserWay.org](https://userway.org/) con la cuenta asignada:
   - **Correo:** `soporte.gestvet@gmail.com`
   - **Contraseña:** `12345678gestvet`
2. Registra la URL pública de tu aplicación desplegada (ejemplo: `https://gestvet.vercel.app`).
3. Copia el **Account ID** que te proporcione UserWay y agrégalo en la variable de entorno `VITE_USERWAY_ACCOUNT_ID` de tu frontend Vercel/Netlify.
4. El widget flotante de accesibilidad (icono azul con persona) aparecerá automáticamente en la esquina de tu sitio web.

---

## 6. Lista de Comprobación Final (Checklist)

- [x] Favicons oficiales (`favicon.ico`, `favicon.png`, `gestvet-icon.png`) cargados en la pestaña.
- [x] Isotipo oficial (huella con corazón calado en degradado azul/cian) renderizado en la cabecera.
- [x] Aceptación obligatoria de **Términos y Condiciones** requerida en el registro.
- [x] Asistente de IA (OpenRouter) configurado con fallback automático.
- [ ] Migraciones de base de datos aplicadas en el PostgreSQL remoto (`alembic upgrade head`).
- [ ] Dominio configurado en la consola de UserWay (`soporte.gestvet@gmail.com`).
