import { useQuery } from '@tanstack/react-query'

import { fetchVeterinarianAlerts, veterinarianAlertsQueryKey } from '../../api/insights'
import DataTable, { type DataColumn } from '../../components/DataTable'
import SectionCard from '../../components/SectionCard'

type Alerta = Awaited<ReturnType<typeof fetchVeterinarianAlerts>>['items'][number]

const COLUMNAS: readonly DataColumn<Alerta>[] = [
  { id: 'veterinario', header: 'Veterinario', cell: (item) => item.veterinarian_name },
  { id: 'resenas', header: 'Reseñas bajas (60 días)', cell: (item) => item.low_rating_count },
  { id: 'reclamos', header: 'Reclamos (60 días)', cell: (item) => item.complaint_count },
]

export default function VeterinarianAlertsSection() {
  const alertas = useQuery({
    queryKey: veterinarianAlertsQueryKey,
    queryFn: fetchVeterinarianAlerts,
  })

  return (
    <SectionCard
      title="Veterinarios a seguir de cerca"
      description="Tres o más reseñas de 1-2 estrellas, o dos o más reclamos, en los últimos 60 días."
    >
      <DataTable
        columns={COLUMNAS}
        data={alertas.data?.items ?? []}
        isLoading={alertas.isPending}
        emptyMessage="Ningún veterinario está en ese caso ahora mismo."
        getRowId={(item) => String(item.veterinarian_id)}
      />
    </SectionCard>
  )
}
