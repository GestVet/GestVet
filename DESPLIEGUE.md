# Despliegue a producción

Guía paso a paso para poner GestVet en línea, pensada para una clínica chica: prioriza costo bajo y simplicidad de mantenimiento por sobre control total de la infraestructura. No hace falta saber administrar servidores.

## El stack recomendado, y por qué

| Pieza | Servicio | Por qué |
| --- | --- | --- |
| Backend (FastAPI) | [Railway](https://railway.app) | Sin arranque en frío (a diferencia de los planes gratuitos de otros PaaS), precio por uso real, detecta y arranca un proyecto Python solo. |
| Base de datos | Postgres administrado de Railway (o [Supabase](https://supabase.com) si prefieren un plan gratuito aparte) | Mismo motor que ya usa el proyecto en `docker-compose.yml`; nadie administra backups ni parches a mano. |
| Frontend (React/Vite) | [Vercel](https://vercel.com) | Hecho para builds estáticos de Vite/React; despliega en cada push, con HTTPS y CDN incluidos, plan gratuito alcanza de sobra para esto. |
| Dominio | Cualquier registrador (Namecheap, Google Domains, etc.) | Opcional al principio: los dos servicios de arriba dan una URL propia gratis para empezar. |

Ninguno de los dos exige tarjeta para el plan de entrada, y ambos escalan sin migrar nada si la clínica crece.

## 0. Antes de empezar

- Una cuenta en Railway y otra en Vercel (ambas se pueden crear con la cuenta de GitHub del proyecto).
- El repositorio en GitHub, con `main` como la rama que se despliega.
- `JWT_SECRET_KEY` propio, generado una sola vez y guardado en un gestor de contraseñas, nunca en el repositorio:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

## 1. Base de datos

1. En Railway, crear un proyecto nuevo y agregar un servicio **PostgreSQL** desde su catálogo de plantillas.
2. Railway genera solo una `DATABASE_URL`. Copiarla: hace falta más abajo, con un ajuste (ver paso 3).

## 2. Backend en Railway

1. En el mismo proyecto de Railway, agregar un servicio nuevo **desde el repositorio de GitHub**, apuntado a la carpeta `backend/` (Railway permite fijar el "root directory" del servicio).
2. Railway detecta un proyecto Python. Como este usa `uv`, conviene fijar explícitamente:
   - **Build command**: `uv sync --frozen --no-dev`
   - **Start command**: `uv run uvicorn gestvet.main:app --app-dir src --host 0.0.0.0 --port $PORT`
3. Cargar las variables de entorno del servicio (ver la tabla completa en la sección 5). La más importante para no repetir el error más común: `DATABASE_URL` la copia Railway con el prefijo `postgresql://`, pero este proyecto usa el driver asíncrono `asyncpg`, así que hay que cambiarle el prefijo a `postgresql+asyncpg://` antes de pegarla.
4. Desplegar. El primer build tarda unos minutos.

## 3. Migraciones en producción

La aplicación **no crea tablas sola al arrancar** (ver el README, sección "Base de datos") — eso es deliberado, para que la base nunca se aparte del historial de Alembic sin que nadie se entere. Después de cada despliegue con cambios de esquema, correr una vez:

```bash
railway run --service <nombre-del-servicio-backend> uv run alembic upgrade head
```

(`railway run` ejecuta el comando con las variables de entorno del servicio ya cargadas, así que apunta a la base de producción sin copiar nada a mano.) Automatizar este paso como parte del pipeline de despliegue es la mejora natural una vez que el primer despliegue manual ya funcionó.

## 4. Frontend en Vercel

1. Importar el repositorio en Vercel, con el **root directory** fijado en `frontend/`.
2. Vercel detecta Vite solo. Confirmar:
   - **Build command**: `pnpm build`
   - **Output directory**: `dist`
3. Variable de entorno del proyecto en Vercel:

   ```
   VITE_API_BASE_URL=https://<dominio-del-backend-en-railway>/api/v1
   ```

   A diferencia del desarrollo local (donde el proxy de Vite reenvía `/api` al backend en el mismo origen), en producción el frontend y el backend viven en dominios distintos, así que acá hace falta la URL completa.
4. Desplegar. Cada push a `main` genera un despliegue nuevo automáticamente.

## 5. Variables de entorno del backend

| Variable | Ejemplo en producción | Nota |
| --- | --- | --- |
| `DEBUG` | `false` | Con `true`, la aplicación acepta arrancar con la clave JWT de ejemplo; con `false`, se niega — es la salvaguarda contra desplegar sin haber generado una clave propia. |
| `DATABASE_URL` | `postgresql+asyncpg://usuario:clave@host:5432/gestvet` | La que da Railway, con el prefijo cambiado a `+asyncpg` (ver paso 2.3). |
| `JWT_SECRET_KEY` | (32+ bytes generados una sola vez) | Nunca el valor de ejemplo del repositorio. Rotar invalida todos los tokens vivos. |
| `JWT_ALGORITHM` | `HS256` | Sin necesidad de cambiarlo. |
| `ACCESS_TOKEN_TTL_SECONDS` | `3600` | Cuánto dura un token antes de pedir credenciales de nuevo. |
| `CORS_ALLOWED_ORIGINS` | `["https://app.tudominio.com"]` | El dominio real del frontend en Vercel (o el dominio propio, una vez configurado). Sin esto, el navegador bloquea las peticiones del frontend al backend. |
| `FRONTEND_BASE_URL` | `https://app.tudominio.com` | Con qué dominio arma el enlace del correo de "olvidé mi contraseña". |
| `API_BASE_URL` | `https://api.tudominio.com` | Con qué dominio arma la URL de un adjunto de la historia clínica. |
| `ATTACHMENTS_STORAGE_DIR` | `/data/attachments` | Ver la advertencia de la sección 6: tiene que apuntar a un volumen persistente, no al disco efímero del contenedor. |

## 6. Adjuntos de la historia clínica — atención acá

Hoy los adjuntos (fotos, PDFs de la historia clínica, evidencia de un reclamo) se guardan en el disco del propio servidor (`LocalDiskAttachmentStorage`, ver el README). En Railway, el disco de un servicio es **efímero** por defecto: un redespliegue puede borrar todo lo que se subió.

Dos caminos, en orden de qué tan pronto conviene resolverlo:

1. **Ahora, para salir a producción**: montar un [volumen persistente de Railway](https://docs.railway.app/reference/volumes) en la ruta que apunte `ATTACHMENTS_STORAGE_DIR`. Sencillo, y alcanza mientras el volumen de archivos sea chico.
2. **Más adelante, para no depender de un solo servidor**: escribir un adaptador que satisfaga el mismo puerto (`AttachmentStorage`) contra un bucket compatible con S3 (Amazon S3, Cloudflare R2, Backblaze B2). El código ya está preparado para este cambio — es la misma idea que ya explica el propio adaptador de correo y el de WhatsApp: se reemplaza la clase, ningún caso de uso cambia.

**No lo dejen sin resolver de alguna de las dos formas**: perder un adjunto de la historia clínica de una mascota no es un detalle menor.

## 7. Dominio propio (opcional)

Railway y Vercel dan una URL gratuita (`*.up.railway.app` y `*.vercel.app`) que ya sirve HTTPS. Para usar un dominio propio:

1. Comprar el dominio en cualquier registrador.
2. En Vercel: **Settings → Domains**, agregar `app.tudominio.com` y seguir las instrucciones de DNS (un registro `CNAME`).
3. En Railway: **Settings → Networking → Custom Domain**, agregar `api.tudominio.com`, mismo mecanismo.
4. Actualizar `CORS_ALLOWED_ORIGINS`, `FRONTEND_BASE_URL`, `API_BASE_URL` (backend) y `VITE_API_BASE_URL` (frontend) con los dominios definitivos, y volver a desplegar ambos.

## 8. Verificación después de desplegar

En orden, contra la URL real de producción:

1. `GET https://api.tudominio.com/api/v1/health` responde `{"status": "ok", ...}`.
2. Registrar un cliente de prueba desde el frontend, confirmar que el correo de recuperación de contraseña (si se probó) llega con el enlace correcto (usa `FRONTEND_BASE_URL`).
3. Subir un adjunto a una entrada de la historia clínica, recargar la página y comprobar que el archivo se sigue viendo (confirma que el volumen persistente de la sección 6 quedó bien montado).
4. Revisar los logs del backend en Railway: cualquier confirmación de cita o de pago por QR que se pruebe tiene que aparecer ahí como un mensaje de WhatsApp simulado (`WhatsApp a ...`), mientras no exista una cuenta real conectada.

## 9. Después de esto

- **WhatsApp Business API real**: ver la sección dedicada en el `README.md` — es un trámite de la clínica ante Meta (o un intermediario), no un cambio de infraestructura de este despliegue.
- **CI/CD**: GitHub Actions ya corre lint, arquitectura y pruebas en cada push (ver el README). El paso que falta es que ese mismo flujo dispare las migraciones de la sección 3 automáticamente contra producción tras cada merge a `main`, en vez de correrlas a mano.
- **Copias de seguridad de la base**: Railway y Supabase ofrecen backups automáticos de Postgres en sus planes pagos — conviene activarlos antes de tener datos reales de clientes.
