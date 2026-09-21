import type { AppointmentResponse } from '../../api/types'
import { useCan } from '../../store/session'
import AppointmentTypeCell from './AppointmentTypeCell'
import { fechaYHora } from './appointmentSummary'

interface AppointmentHeaderProps {
  readonly cita: AppointmentResponse
}

/**
 * De quién es la cita y con quién, arriba del detalle.
 *
 * El cliente ya sabe que la cita es suya: ve al veterinario. Quien atiende ya
 * sabe que es suya: ve al cliente. La administración ve a los dos.
 */
export default function AppointmentHeader({ cita }: AppointmentHeaderProps) {
  const verCliente = useCan('clients.read')
  const verVeterinario = !useCan('appointments.attend')
  const datos = [
    { etiqueta: 'Mascota', valor: cita.pet_name, visible: true },
    { etiqueta: 'Cliente', valor: cita.client_name, visible: verCliente },
    { etiqueta: 'Veterinario', valor: cita.veterinarian_name, visible: verVeterinario },
    {
      etiqueta: 'Fecha',
      valor: `${fechaYHora(cita.scheduled_at)} (${String(cita.duration_minutes)} min)`,
      visible: true,
    },
  ].filter((dato) => dato.visible)

  return (
    <dl className="m-0 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-5">
      {datos.map((dato) => (
        <div key={dato.etiqueta} className="flex min-w-0 flex-col gap-0.5">
          <dt className="text-muted-foreground">{dato.etiqueta}</dt>
          <dd className="m-0 font-medium break-words">{dato.valor === '' ? '—' : dato.valor}</dd>
        </div>
      ))}
      <div className="flex min-w-0 flex-col gap-0.5">
        <dt className="text-muted-foreground">Tipo</dt>
        <dd className="m-0 font-medium">
          <AppointmentTypeCell
            name={cita.appointment_type_name}
            isEmergency={cita.is_emergency}
          />
        </dd>
      </div>
    </dl>
  )
}
