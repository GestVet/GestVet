import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  appointmentsQueryKey,
  cancelAppointment,
  completeAppointment,
  confirmAppointment,
} from '../../api/appointments'
import type { AppointmentResponse } from '../../api/types'
import Icon from '../../components/Icon'
import { useIsVeterinarian } from '../../store/session'

interface AppointmentActionsProps {
  readonly appointment: AppointmentResponse
}

/**
 * Los botones de una fila de la tabla de citas.
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
  const cancelar = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => cancelAppointment(id, motivo),
    onSuccess: refrescar,
  })

  const ocupado = confirmar.isPending || completar.isPending || cancelar.isPending
  const abierta = appointment.status === 'pending' || appointment.status === 'confirmed'

  const pedirCancelacion = () => {
    // El backend exige un motivo, así que la interfaz lo pide antes de enviar.
    const motivo = window.prompt('¿Por qué se cancela la cita?')
    if (motivo !== null && motivo.trim() !== '') {
      cancelar.mutate({ id: appointment.id, motivo })
    }
  }

  return (
    <div className="row-actions">
      {atiende && appointment.status === 'pending' ? (
        <button
          type="button"
          className="btn btn-blue"
          disabled={ocupado}
          onClick={() => {
            confirmar.mutate(appointment.id)
          }}
        >
          <Icon name="confirmar" size={14} />
          <span>Confirmar</span>
        </button>
      ) : null}

      {atiende && appointment.status === 'confirmed' ? (
        <button
          type="button"
          className="btn btn-green"
          disabled={ocupado}
          onClick={() => {
            completar.mutate(appointment.id)
          }}
        >
          <Icon name="confirmar" size={14} />
          <span>Completar</span>
        </button>
      ) : null}

      {abierta ? (
        <button type="button" className="btn btn-danger" disabled={ocupado} onClick={pedirCancelacion}>
          <Icon name="cancelar" size={14} />
          <span>Cancelar</span>
        </button>
      ) : null}
    </div>
  )
}
