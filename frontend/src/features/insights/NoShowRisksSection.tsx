import { useQuery } from '@tanstack/react-query'

import { fetchNoShowRisks, noShowRisksQueryKey } from '../../api/insights'
import DataTable, { type DataColumn } from '../../components/DataTable'
import SectionCard from '../../components/SectionCard'

type Riesgo = Awaited<ReturnType<typeof fetchNoShowRisks>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Riesgo>[] = [
  { id: 'cita', header: 'Cita', cell: (item) => `#${String(item.appointment_id)}` },
  { id: 'cliente', header: 'Cliente', cell: (item) => item.client_name },
  { id: 'mascota', header: 'Mascota', cell: (item) => item.pet_name },
  { id: 'cuando', header: 'Cuándo', cell: (item) => FORMATO.format(new Date(item.scheduled_at)) },
  { id: 'previas', header: 'Inasistencias previas', cell: (item) => item.past_incidents },
]

export default function NoShowRisksSection() {
  const riesgos = useQuery({ queryKey: noShowRisksQueryKey, queryFn: fetchNoShowRisks })

  return (
    <SectionCard
      title="Riesgo de inasistencia"
      description="Citas próximas de clientes con dos o más citas pasadas que quedaron sin cerrar. Vale la pena llamar para confirmar."
    >
      <DataTable
        columns={COLUMNAS}
        data={riesgos.data?.items ?? []}
        isLoading={riesgos.isPending}
        emptyMessage="No hay citas con riesgo de inasistencia."
        getRowId={(item) => String(item.appointment_id)}
      />
    </SectionCard>
  )
}
