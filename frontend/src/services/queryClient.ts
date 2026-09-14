import { QueryClient } from '@tanstack/react-query'

import { debeReintentar } from './api'

/**
 * El caché de datos de la aplicación.
 *
 * Vive en su propio módulo, y no dentro de `main.tsx`, para que la sesión lo
 * vacíe al cerrarse: los datos de una cuenta no pueden quedar a la vista de la
 * siguiente que entra en el mismo navegador.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: debeReintentar,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})
