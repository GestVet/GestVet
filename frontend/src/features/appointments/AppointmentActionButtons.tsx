import type { AppointmentStatus } from '../../api/types'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'

interface AppointmentActionButtonsProps {
  readonly status: AppointmentStatus
  readonly atiende: boolean
  readonly ocupado: boolean
  readonly onConfirm: () => void
  readonly onComplete: () => void
  readonly onMarkNoShow: () => void
}

/** Los botones de quien atiende una cita, ya resueltos según su estado. */
export default function AppointmentActionButtons({
  status,
  atiende,
  ocupado,
  onConfirm,
  onComplete,
  onMarkNoShow,
}: AppointmentActionButtonsProps) {
  if (!atiende) {
    return null
  }
  const abierta = status === 'pending' || status === 'confirmed'

  return (
    <>
      {status === 'pending' ? (
        <Button type="button" size="sm" disabled={ocupado} onClick={onConfirm}>
          <Icon name="confirmar" size={14} />
          <span>Confirmar</span>
        </Button>
      ) : null}

      {status === 'confirmed' ? (
        <Button type="button" size="sm" variant="success" disabled={ocupado} onClick={onComplete}>
          <Icon name="confirmar" size={14} />
          <span>Completar</span>
        </Button>
      ) : null}

      {abierta ? (
        <Button type="button" size="sm" variant="outline" disabled={ocupado} onClick={onMarkNoShow}>
          <Icon name="alerta" size={14} />
          <span>No asistió</span>
        </Button>
      ) : null}
    </>
  )
}
