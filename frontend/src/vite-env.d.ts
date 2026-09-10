/// <reference types="vite/client" />

/**
 * Tipos de las variables de entorno del proyecto.
 *
 * Sin esto, `import.meta.env.LO_QUE_SEA` es `any` y el linter estricto lo
 * rechaza, que es exactamente lo que debe hacer.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
