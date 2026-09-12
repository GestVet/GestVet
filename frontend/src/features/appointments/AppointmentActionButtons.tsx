import type { AppointmentStatus } from '../../api/types'
import Icon from '../../components/Icon'

interface AppointmentActionButtonsProps {
  readonly status: AppointmentStatus
  readonly atiende: boolean
  readonly ocupado: boolean
  readonly onConfirm: () => void
  readonly onComplete: () => void
  readonly onMarkNoShow: () => void
  readonly onCancel: () => void
}

/** Los botones de una fila de citas, ya resueltos según rol y estado. */
export default function AppointmentActionButtons({
  status,
  atiende,
  ocupado,
  onConfirm,
  onComplete,
  onMarkNoShow,
  onCancel,
}: AppointmentActionButtonsProps) {
  const abierta = status === 'pending' || status === 'confirmed'

  return (
    <div className="row-actions">
      {atiende && status === 'pending' ? (
        <button type="button" className="btn btn-blue" disabled={ocupado} onClick={onConfirm}>
          <Icon name="confirmar" size={14} />
          <span>Confirmar</span>
        </button>
      ) : null}

      {atiende && status === 'confirmed' ? (
        <button type="button" className="btn btn-green" disabled={ocupado} onClick={onComplete}>
          <Icon name="confirmar" size={14} />
          <span>Completar</span>
        </button>
      ) : null}

      {atiende && abierta ? (
        <button type="button" className="btn btn-plain" disabled={ocupado} onClick={onMarkNoShow}>
          <Icon name="alerta" size={14} />
          <span>No asistió</span>
        </button>
      ) : null}

      {abierta ? (
        <button type="button" className="btn btn-danger" disabled={ocupado} onClick={onCancel}>
          <Icon name="cancelar" size={14} />
          <span>Cancelar</span>
        </button>
      ) : null}
    </div>
  )
}
