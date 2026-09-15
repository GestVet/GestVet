import { useQuery } from '@tanstack/react-query'

import { fetchPetsOverview, petsOverviewQueryKey } from '../../api/insights'
import EmptyState from '../../components/EmptyState'
import PageHeader from '../../components/PageHeader'
import PetOverviewSection from './PetOverviewSection'

export default function PetsOverviewView() {
  const panorama = useQuery({
    queryKey: petsOverviewQueryKey,
    queryFn: fetchPetsOverview,
  })

  const items = panorama.data?.items ?? []
  const activas = items.filter((item) => item.is_active)
  const inactivas = items.filter((item) => !item.is_active)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Panorama de mascotas"
        description="Todas las mascotas registradas, filtrables por especie, estado de vacunación y peso."
      />

      {panorama.isPending ? (
        <EmptyState title="Cargando…" />
      ) : (
        <>
          <PetOverviewSection
            titulo="Mascotas activas"
            descripcion="Filtrá la tabla y los gráficos se actualizan con lo que quede visible."
            items={activas}
            idPrefix="activas"
          />
          <PetOverviewSection
            titulo="Mascotas inactivas"
            descripcion="Mascotas dadas de baja."
            items={inactivas}
            idPrefix="inactivas"
            collapsible
            defaultOpen={false}
          />
        </>
      )}
    </div>
  )
}
