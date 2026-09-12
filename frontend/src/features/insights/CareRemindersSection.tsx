import { useQuery } from '@tanstack/react-query'

import { careRemindersQueryKey, fetchCareReminders } from '../../api/insights'
import DataTable, { type DataColumn } from '../../components/DataTable'
import SectionCard from '../../components/SectionCard'

type Recordatorio = Awaited<ReturnType<typeof fetchCareReminders>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium' })

const COLUMNAS: readonly DataColumn<Recordatorio>[] = [
  { id: 'mascota', header: 'Mascota', cell: (item) => item.pet_name },
  { id: 'dueno', header: 'Dueño', cell: (item) => item.owner_name },
  { id: 'motivo', header: 'Motivo', cell: (item) => item.reason_label },
  {
    id: 'ultima',
    header: 'Última vez',
    cell: (item) =>
      item.last_occurred_at ? FORMATO.format(new Date(item.last_occurred_at)) : 'Nunca',
  },
]

export default function CareRemindersSection() {
  const recordatorios = useQuery({
    queryKey: careRemindersQueryKey,
    queryFn: fetchCareReminders,
  })

  return (
    <SectionCard
      title="Cuidado vencido"
      description="Mascotas sin vacuna hace más de un año o sin control hace más de medio año."
    >
      <DataTable
        columns={COLUMNAS}
        data={recordatorios.data?.items ?? []}
        isLoading={recordatorios.isPending}
        emptyMessage="No hay recordatorios pendientes."
        getRowId={(item, index) => `${String(item.pet_id)}-${item.reason_label}-${String(index)}`}
      />
    </SectionCard>
  )
}
