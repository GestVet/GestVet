# GestVet

Sistema web responsive para la gestión veterinaria: usuarios, mascotas, disponibilidad, citas, analítica e inteligencia asistida.

## Forma del repositorio

Es un monorepositorio con un backend en Python y un frontend en TypeScript, gobernado desde la raíz por un único espacio de trabajo de pnpm.

```text
backend/     API en Python
frontend/    interfaz en TypeScript
.husky/      hooks de Git compartidos
```

La raíz no aloja código de aplicación. Su trabajo es sostener los hooks de Git y los atajos de verificación que valen para ambos lados.

## Requisitos

- Python 3.12 a 3.14
- Node.js 24+
- `uv`
- `pnpm` 12
- Docker Desktop

## Puesta en marcha

```powershell
pnpm install
```

Eso instala el monorepositorio entero y activa los hooks de Git de Husky.

## Convenciones iniciales

- API versionada desde `/api/v1/`.
- Fechas en UTC y conversiones únicamente en la interfaz.
- Listados paginados y filtrables desde el backend.
- Autorización por rol y propiedad del recurso, aplicada acotando el conjunto de datos antes de tocar un objeto por identificador.
- El rol nunca llega desde el cliente: el servidor lo fija.
- Las consultas BI no deben modificar el modelo transaccional.
- Las funciones de IA nunca ejecutan SQL libre ni reciben datos fuera de los permisos del usuario.
- Los secretos solo viven en archivos `.env` locales o en el gestor de secretos del despliegue.
- Los hooks de Git los gestiona Husky desde `.husky/`. El hook `commit-msg` rechaza líneas `Co-authored-by`.
