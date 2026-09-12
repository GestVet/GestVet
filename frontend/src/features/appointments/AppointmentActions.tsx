import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  appointmentsQueryKey,
  cancelAppointment,
  completeAppointment,
  confirmAppointment,
  markAppointmentNoShow,
} from '../../api/appointments'
import type { AppointmentResponse } from '../../api/types'
import { useIsVeterinarian } from '../../store/session'
import AppointmentActionButtons from './AppointmentActionButtons'

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
  const atiende = useIsVeterinarian()
  const queryClient = useQueryClient()

  const refrescar = async () => {
    await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
  }

  const confirmar = useMutation({ mutationFn: confirmAppointment, onSuccess: refrescar })
  const completar = useMutation({ mutationFn: completeAppointment, onSuccess: refrescar })
  const marcarNoAsistio = useMutation({ mutationFn: markAppointmentNoShow, onSuccess: refrescar })
  const cancelar = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => cancelAppointment(id, motivo),
    onSuccess: refrescar,
  })

  const ocupado =
    confirmar.isPending || completar.isPending || cancelar.isPending || marcarNoAsistio.isPending

  const pedirCancelacion = () => {
    // El backend exige un motivo, así que la interfaz lo pide antes de enviar.
    const motivo = window.prompt('¿Por qué se cancela la cita?')
    if (motivo !== null && motivo.trim() !== '') {
      cancelar.mutate({ id: appointment.id, motivo })
    }
  }

  return (
    <AppointmentActionButtons
      status={appointment.status}
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
      onCancel={pedirCancelacion}
    />
  )
}
