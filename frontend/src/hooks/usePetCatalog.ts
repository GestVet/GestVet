import { useQuery } from '@tanstack/react-query'

import { fetchPetCatalog, petCatalogQueryKey } from '../api/pets'
import type { SpeciesResponse } from '../api/types'

/**
 * El catálogo de especies y razas que acepta el servidor.
 *
 * Vive en el código del servidor y solo cambia con un despliegue, así que se
 * pide una vez por sesión. Vive en `hooks/` porque lo usan componentes, que no
 * pueden importar `api/` directo.
 */
export function usePetCatalog() {
  const catalogo = useQuery({
    queryKey: petCatalogQueryKey,
    queryFn: fetchPetCatalog,
    staleTime: Infinity,
  })
  const especies: readonly SpeciesResponse[] = catalogo.data?.species ?? []

  return {
    especies,
    isPending: catalogo.isPending,
    razasDe: (especie: string): readonly string[] =>
      especies.find((item) => item.name === especie)?.breeds ?? [],
  }
}
