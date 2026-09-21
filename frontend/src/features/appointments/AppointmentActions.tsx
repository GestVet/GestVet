import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  appointmentsQueryKey,
  completeAppointment,
  confirmAppointment,
  markAppointmentNoShow,
} from '../../api/appointments'
import type { AppointmentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import { errorMessage } from '../../services/api'
import { useCan } from '../../store/session'
import AppointmentActionButtons from './AppointmentActionButtons'
import CancelAppointmentDialog from './CancelAppointmentDialog'

interface AppointmentActionsProps {
  readonly appointment: AppointmentResponse
}

/**
 * Conecta los botones de una fila de citas con sus mutaciones.
 *
 * Qué botón aparece depende del rol y del estado, que es la misma regla que
 * aplica el servidor. Acá solo evita ofrecer una acción que va a ser rechazada.
 */
export default function AppointmentActions({ appointment }: AppointmentActionsProps) {
  const atiende = useCan('appointments.attend')
  const queryClient = useQueryClient()

  const refrescar = async () => {
    await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
  }

  const confirmar = useMutation({ mutationFn: confirmAppointment, onSuccess: refrescar })
  const completar = useMutation({ mutationFn: completeAppointment, onSuccess: refrescar })
  const marcarNoAsistio = useMutation({ mutationFn: markAppointmentNoShow, onSuccess: refrescar })

  const ocupado = confirmar.isPending || completar.isPending || marcarNoAsistio.isPending
  const fallo = [confirmar.error, completar.error, marcarNoAsistio.error].find(
    (error) => error !== null,
  )
  const abierta = appointment.status === 'pending' || appointment.status === 'confirmed'

  return (
    <div className="flex flex-col items-start gap-2 whitespace-normal">
      <div className="flex flex-wrap gap-2">
        <AppointmentActionButtons
          cita={appointment}
          atiende={atiende}
          ocupado={ocupado}
          onConfirm={() => {
            confirmar.mutate(appointment.id)
          }}
          onComplete={() => {
            completar.mutate(appointment.id)
          }}
          onMarkNoShow={() => {
            marcarNoAsistio.mutate(appointment.id)
          }}
        />
        {abierta ? <CancelAppointmentDialog appointmentId={appointment.id} /> : null}
      </div>
      {fallo === undefined ? null : (
        <FormMessage tone="error">{errorMessage(fallo, 'No se pudo actualizar la cita.')}</FormMessage>
      )}
    </div>
  )
}
