import { useQuery } from '@tanstack/react-query'

import { appointmentsQueryKey, fetchAppointments } from '../../api/appointments'
import type { AppointmentStatus } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import TableShell from '../../components/TableShell'
import AppointmentActions from './AppointmentActions'

const COLUMNAS = ['Fecha', 'Duración', 'Estado', 'Descripción', 'Acciones'] as const

// El tono de la etiqueta sale del estado, y el estado viene del contrato: si
// el backend agrega uno nuevo, este mapa deja de compilar.
const TONO: Record<AppointmentStatus, string> = {
  pending: 'pending',
  confirmed: 'confirmed',
  completed: 'completed',
  cancelled: 'cancelled',
}

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function AppointmentsView() {
  const citas = useQuery({ queryKey: appointmentsQueryKey, queryFn: fetchAppointments })
  const items = citas.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Citas</h1>
      </div>

      <section className="card">
        <TableShell
          columns={COLUMNAS}
          isLoading={citas.isPending}
          isEmpty={items.length === 0}
          emptyMessage="No hay citas para mostrar."
        >
          {items.map((cita) => (
            <tr key={cita.id}>
              <td>{FORMATO.format(new Date(cita.scheduled_at))}</td>
              <td>{cita.duration_minutes} min</td>
              <td>
                <StatusBadge label={cita.status_label} tone={TONO[cita.status]} />
                {cita.cancellation_reason ? (
                  <p className="muted">{cita.cancellation_reason}</p>
                ) : null}
              </td>
              <td>{cita.description}</td>
              <td>
                <AppointmentActions appointment={cita} />
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
