import type { AppointmentResponse } from '../../api/types'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { resumenDeCita } from './appointmentSummary'
import CloseAppointmentButton from './CloseAppointmentButton'
import { useNow } from './useNow'

interface AppointmentActionButtonsProps {
  readonly cita: AppointmentResponse
  readonly atiende: boolean
  readonly ocupado: boolean
  readonly onConfirm: () => void
  readonly onComplete: () => void
  readonly onMarkNoShow: () => void
}

/** Los botones de quien atiende una cita, ya resueltos según su estado. */
export default function AppointmentActionButtons({
  cita,
  atiende,
  ocupado,
  onConfirm,
  onComplete,
  onMarkNoShow,
}: AppointmentActionButtonsProps) {
  const ahora = useNow()
  if (!atiende) {
    return null
  }
  const abierta = cita.status === 'pending' || cita.status === 'confirmed'
  const resumen = resumenDeCita(cita)

  return (
    <>
      {cita.status === 'pending' ? (
        <Button type="button" size="sm" disabled={ocupado} onClick={onConfirm}>
          <Icon name="confirmar" size={14} />
          <span>Confirmar</span>
        </Button>
      ) : null}

      {cita.status === 'confirmed' ? (
        <CloseAppointmentButton
          label="Completar"
          icon="confirmar"
          variant="success"
          availableFrom={cita.completable_from}
          now={ahora}
          busy={ocupado}
          dialogTitle="¿Dar la cita por completada?"
          dialogDescription={`Vas a marcar como completada ${resumen}. Después no se puede deshacer.`}
          onConfirm={onComplete}
        />
      ) : null}

      {abierta ? (
        <CloseAppointmentButton
          label="No asistió"
          icon="alerta"
          variant="outline"
          availableFrom={cita.no_show_from}
          now={ahora}
          busy={ocupado}
          dialogTitle="¿Marcar la inasistencia?"
          dialogDescription={`Vas a registrar que nadie se presentó a ${resumen}. Después no se puede deshacer.`}
          onConfirm={onMarkNoShow}
        />
      ) : null}
    </>
  )
}
