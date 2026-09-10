# Frontend de GestVet

React 19 + Vite 8 + TypeScript 6, consumiendo el API de Django Ninja bajo `/api/v1`.

La instalación, las variables de entorno y los comandos de validación están documentados en el README de la raíz del repositorio.

## Comandos

```bash
pnpm dev           # servidor de desarrollo en http://localhost:5173
pnpm build         # verificación de tipos y compilación de producción
pnpm preview       # sirve la compilación de producción
pnpm generate:api  # regenera src/api/schema.d.ts desde el OpenAPI del backend
```

`pnpm dev` hace proxy de `/api` hacia `http://127.0.0.1:8000`, así que el backend debe estar corriendo para que las pantallas tengan datos.

## Organización

- `src/api/` contrato generado desde OpenAPI, alias de tipos y funciones de consulta.
- `src/components/` piezas de interfaz compartidas.
- `src/features/` una carpeta por módulo de dominio, con el mismo nombre que su app de Django.
- `src/router/` rutas y guardas por rol.
- `src/services/` cliente HTTP centralizado.
- `src/store/` estado de cliente con Zustand.

Los componentes no llaman a `axios` directamente: pasan por `src/services/api.ts` y por las funciones de `src/api/`.
