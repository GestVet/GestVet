import { useQuery } from '@tanstack/react-query'

import { fetchPetsOverview, petsOverviewQueryKey } from '../../api/insights'
import EmptyState from '../../components/EmptyState'
import PetOverviewSection from './PetOverviewSection'

/** Las dos tablas de mascotas (activas/inactivas) de "Panorama de la clínica". */
export default function PetsOverviewSections() {
  const panorama = useQuery({
    queryKey: petsOverviewQueryKey,
    queryFn: fetchPetsOverview,
  })

  if (panorama.isPending) {
    return <EmptyState title="Cargando…" />
  }

  const items = panorama.data?.items ?? []
  return (
    <>
      <PetOverviewSection
        titulo="Mascotas activas"
        descripcion="Filtrá la tabla y los gráficos se actualizan con lo que quede visible."
        items={items.filter((item) => item.is_active)}
        idPrefix="activas"
      />
      <PetOverviewSection
        titulo="Mascotas inactivas"
        descripcion="Mascotas dadas de baja."
        items={items.filter((item) => !item.is_active)}
        idPrefix="inactivas"
        collapsible
        defaultOpen={false}
      />
    </>
  )
}
