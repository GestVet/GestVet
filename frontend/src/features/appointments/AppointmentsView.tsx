import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  type AppointmentsFilter,
  appointmentsFilterQueryKey,
  fetchAppointments,
} from '../../api/appointments'
import type { AppointmentStatus } from '../../api/types'
import TableShell from '../../components/TableShell'
import { useIsVeterinarian } from '../../store/session'
import AppointmentRow from './AppointmentRow'
import AppointmentsFilters from './AppointmentsFilters'

const COLUMNAS = ['Fecha', 'Duración', 'Estado', 'Descripción', 'Acciones'] as const

export default function AppointmentsView() {
  const atiende = useIsVeterinarian()
  const [estado, setEstado] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [soloEmergencias, setSoloEmergencias] = useState(false)

  const filtro: AppointmentsFilter = {
    status: estado === '' ? undefined : (estado as AppointmentStatus),
    starts_after: desde === '' ? undefined : new Date(desde).toISOString(),
    ends_before: hasta === '' ? undefined : new Date(hasta).toISOString(),
    is_emergency: soloEmergencias ? true : undefined,
  }

  const citas = useQuery({
    queryKey: appointmentsFilterQueryKey(filtro),
    queryFn: () => fetchAppointments(filtro),
  })
  const items = citas.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Citas</h1>
      </div>

      <section className="card">
        <AppointmentsFilters
          estado={estado}
          desde={desde}
          hasta={hasta}
          soloEmergencias={soloEmergencias}
          mostrarEmergencias={atiende}
          onEstadoChange={setEstado}
          onDesdeChange={setDesde}
          onHastaChange={setHasta}
          onSoloEmergenciasChange={setSoloEmergencias}
        />

        <TableShell
          columns={COLUMNAS}
          isLoading={citas.isPending}
          isEmpty={items.length === 0}
          emptyMessage="No hay citas para mostrar."
        >
          {items.map((cita) => (
            <AppointmentRow key={cita.id} cita={cita} />
          ))}
        </TableShell>
      </section>
    </div>
  )
}
