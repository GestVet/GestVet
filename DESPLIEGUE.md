# Despliegue a Producción (Render Free + Supabase + Vercel)

> [!NOTE]
> La guía completa, detallada y actualizada paso a paso para el despliegue se encuentra en [**DEPLOYMENT.md**](DEPLOYMENT.md).

Esta arquitectura está optimizada para operar con costo cero (planes gratuitos) sin comprometer la integridad de los datos de la clínica veterinaria.

---

## El Stack Oficial de Producción

| Pieza | Servicio / Plan | Rol y Justificación |
| --- | --- | --- |
| **Backend API** | [Render](https://render.com) (Plan **Free**) | Web Service Python 3.13 con `uv`. Se despliega automáticamente con el Blueprint [`render.yaml`](render.yaml). |
| **Base de Datos** | [Supabase](https://supabase.com) (PostgreSQL) | PostgreSQL administrado con alta disponibilidad. Se conecta a través del **Session Pooler** (puerto `5432`). |
| **Adjuntos / Archivos** | [Supabase Storage](https://supabase.com) (Bucket público `attachments`) | Almacenamiento persistente en la nube (`SupabaseAttachmentStorage`) para radiografías, análisis y reclamos. Resuelve la limitación del disco efímero de Render Free. |
| **Frontend SPA** | [Vercel](https://vercel.com) (Plan Hobby) | Build estático de React + Vite con CDN global HTTPS. |
| **Cron de Recordatorios** | [GitHub Actions](https://github.com) | Flujo [`.github/workflows/reminders-cron.yml`](.github/workflows/reminders-cron.yml) ejecutado cada 30 min de lunes a viernes (hora de Lima) para despertar al backend y enviar avisos de WhatsApp. |

---

## Puntos Clave de la Arquitectura

### 1. Adjuntos en Supabase Storage (sin disco persistente en Render)
En el plan Free de Render no hay disco persistente: los contenedores se destruyen y recrean en cada despliegue o ciclo de reposo. Para evitar la pérdida de historias clínicas y evidencias de reclamos:
- Los archivos se almacenan en un bucket público de Supabase Storage mediante la API REST (`httpx`).
- Se configuran las variables `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_STORAGE_BUCKET=attachments`.
- Si estas variables no están presentes (entornos locales de desarrollo y pruebas), el backend utiliza automáticamente almacenamiento local en disco (`LocalDiskAttachmentStorage`).

### 2. Conexión a la Base de Datos (Session Pooler)
- Se debe utilizar la cadena del **Session Pooler** de Supabase (puerto `5432`) anteponiendo el driver asíncrono `postgresql+asyncpg://`.
- **NO** usar conexión Directa (sólo resuelve a IPv6, incompatible con Render).
- **NO** usar Transaction Pooler (puerto `6543`, rompe con prepared statements en `asyncpg`).

### 3. Recordatorios y Reposo de Render Free
Render Free suspende el servicio web tras 15 minutos sin peticiones HTTP. El flujo programado en GitHub Actions realiza un `POST` con reintentos y tiempo de espera de 90s hacia `/api/v1/internal/reminders/run` usando el token `REMINDERS_CRON_TOKEN`, garantizando el envío periódico de avisos aunque no haya tráfico activo en la web.

Para el detalle paso a paso de variables de entorno, checklist y configuración, consulta [**DEPLOYMENT.md**](DEPLOYMENT.md).
