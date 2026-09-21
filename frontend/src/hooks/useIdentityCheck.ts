import { useQuery } from '@tanstack/react-query'

import { fetchIdentityCheck, identityCheckQueryKey } from '../api/auth'

/**
 * Si la verificación de DNI con RENIEC está en uso.
 *
 * Hoy no lo está: falta el convenio. Mientras tanto no se pide autorización
 * para una consulta que no ocurre ni se ofrece completar nombres desde el DNI.
 * Mientras responde se asume que no, para no mostrar una casilla que después
 * desaparece. Vive en `hooks/` porque lo usan el registro y el alta exprés.
 */
export function useIdentityCheck(): boolean {
  const estado = useQuery({
    queryKey: identityCheckQueryKey,
    queryFn: fetchIdentityCheck,
    staleTime: Infinity,
  })
  return estado.data?.available ?? false
}
