import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import {
  type AppointmentsFilter,
  appointmentsFilterQueryKey,
  fetchAppointments,
} from '../../api/appointments'
import type { AppointmentResponse, AppointmentStatus } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
import { instanteEnClinica, sumarDias } from '../../services/clinicTime'
import RowExpandButton from '../../components/RowExpandButton'
import StatusBadge, { type StatusTone } from '../../components/StatusBadge'
import { Card, CardContent } from '../../components/ui/card'
import { useCan } from '../../store/session'
import AppointmentActions from './AppointmentActions'
import AppointmentDetails from './AppointmentDetails'
import AppointmentsFilters from './AppointmentsFilters'
import AppointmentTypeCell from './AppointmentTypeCell'

// El tono de la etiqueta sale del estado, y el estado viene del contrato: si
// el backend agrega uno nuevo, este mapa deja de compilar.
const TONO: Record<AppointmentStatus, StatusTone> = {
  pending: 'pending',
  confirmed: 'confirmed',
  completed: 'completed',
  cancelled: 'cancelled',
  no_show: 'cancelled',
}

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const ESTADOS: readonly string[] = ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']

function esEstado(valor: string): valor is AppointmentStatus {
  return ESTADOS.includes(valor)
}

const COLUMNAS: readonly DataColumn<AppointmentResponse>[] = [
  {
    id: 'fecha',
    header: 'Fecha',
    cell: (cita) => (
      <div className="flex flex-col">
        <span>{FORMATO.format(new Date(cita.scheduled_at))}</span>
        <span className="text-xs text-muted-foreground">{`${String(cita.duration_minutes)} min`}</span>
      </div>
    ),
  },
  { id: 'mascota', header: 'Mascota', cell: (cita) => cita.pet_name || '—' },
  { id: 'cliente', header: 'Cliente', cell: (cita) => cita.client_name || '—' },
  { id: 'veterinario', header: 'Veterinario', cell: (cita) => cita.veterinarian_name || '—' },
  {
    id: 'tipo',
    header: 'Tipo',
    cell: (cita) => (
      <AppointmentTypeCell name={cita.appointment_type_name} isEmergency={cita.is_emergency} />
    ),
  },
  {
    id: 'estado',
    header: 'Estado',
    className: 'whitespace-normal',
    cell: (cita) => (
      <div className="flex min-w-32 flex-col items-start gap-1">
        <StatusBadge label={cita.status_label} tone={TONO[cita.status]} />
        {cita.cancellation_reason ? (
          <span className="text-xs text-muted-foreground">{cita.cancellation_reason}</span>
        ) : null}
      </div>
    ),
  },
  {
    id: 'descripcion',
    header: 'Descripción',
    className: 'min-w-48 whitespace-normal',
    cell: (cita) => cita.description,
  },
  {
    id: 'acciones',
    header: 'Acciones',
    cell: (cita, fila) => (
      <div className="flex flex-wrap gap-2">
        <AppointmentActions appointment={cita} />
        <RowExpandButton
          isExpanded={fila.isExpanded}
          onToggle={fila.toggleExpanded}
          collapsedLabel="Ver detalle"
          expandedLabel="Ocultar detalle"
        />
      </div>
    ),
  },
]

/**
 * Las columnas que ve cada quien.
 *
 * El cliente ya sabe que la cita es suya: ve al veterinario. Quien atiende ya
 * sabe que es suya: ve al cliente. La administración ve a los dos.
 */
function useColumnas(): readonly DataColumn<AppointmentResponse>[] {
  const verCliente = useCan('clients.read')
  const verVeterinario = !useCan('appointments.attend')
  return useMemo(() => {
    const ocultas = new Set<string>()
    if (!verCliente) {
      ocultas.add('cliente')
    }
    if (!verVeterinario) {
      ocultas.add('veterinario')
    }
    return COLUMNAS.filter((columna) => !ocultas.has(columna.id))
  }, [verCliente, verVeterinario])
}

export default function AppointmentsView() {
  const atiende = useCan('appointments.attend')
  const columnas = useColumnas()
  const [estado, setEstado] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [soloEmergencias, setSoloEmergencias] = useState(false)

  const filtro: AppointmentsFilter = {
    status: esEstado(estado) ? estado : undefined,
    starts_after: desde === '' ? undefined : instanteEnClinica(desde),
    ends_before: hasta === '' ? undefined : instanteEnClinica(sumarDias(hasta, 1)),
    is_emergency: soloEmergencias ? true : undefined,
  }

  const citas = useQuery({
    queryKey: appointmentsFilterQueryKey(filtro),
    queryFn: () => fetchAppointments(filtro),
    // Al cambiar un filtro la tabla sigue mostrando las filas anteriores
    // hasta que llegan las nuevas, en vez de vaciarse con "Cargando…".
    placeholderData: keepPreviousData,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Citas" />

      <Card className="py-5 shadow-sm">
        <CardContent className="px-5">
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
        </CardContent>
      </Card>

      <DataTable
        columns={columnas}
        data={citas.data?.items ?? []}
        isLoading={citas.isPending}
        emptyMessage="No hay citas para mostrar."
        getRowId={(cita) => String(cita.id)}
        pageSize={15}
        renderExpanded={(cita) => <AppointmentDetails cita={cita} />}
      />
    </div>
  )
}
