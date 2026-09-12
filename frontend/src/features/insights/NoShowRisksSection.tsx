import { useQuery } from '@tanstack/react-query'

import { fetchNoShowRisks, noShowRisksQueryKey } from '../../api/insights'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Cita', 'Cliente', 'Mascota', 'Cuándo', 'Inasistencias previas'] as const
const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function NoShowRisksSection() {
  const riesgos = useQuery({ queryKey: noShowRisksQueryKey, queryFn: fetchNoShowRisks })
  const items = riesgos.data?.items ?? []

  return (
    <section className="card">
      <h2>Riesgo de inasistencia</h2>
      <p className="muted">
        Citas próximas de clientes con dos o más citas pasadas que quedaron sin cerrar. Vale la
        pena llamar para confirmar.
      </p>
      <TableShell
        columns={COLUMNAS}
        isLoading={riesgos.isPending}
        isEmpty={items.length === 0}
        emptyMessage="No hay citas con riesgo de inasistencia."
      >
        {items.map((item) => (
          <tr key={item.appointment_id}>
            <td>#{item.appointment_id}</td>
            <td>{item.client_name}</td>
            <td>{item.pet_name}</td>
            <td>{FORMATO.format(new Date(item.scheduled_at))}</td>
            <td>{item.past_incidents}</td>
          </tr>
        ))}
      </TableShell>
    </section>
  )
}
