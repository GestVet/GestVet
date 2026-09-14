import { useMutation, useQueryClient } from '@tanstack/react-query'

import { petCatalogQueryKey } from '../../api/pets'

/** Los largos que acepta el servidor para cada nombre. */
export const MAX_ESPECIE = 40
export const MAX_RAZA = 60

/**
 * Un cambio en el catálogo.
 *
 * Al guardarse vuelve a pedir el catálogo entero: la vista de administración y
 * los formularios de mascotas cuelgan de la misma clave. Las demás pantallas
 * abiertas se enteran por el aviso en tiempo real.
 */
export function useCatalogChange<TVariables>(
  mutationFn: (variables: TVariables) => Promise<unknown>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: petCatalogQueryKey })
    },
  })
}
