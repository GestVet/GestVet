import { Fragment, useState } from 'react'

import type { AppointmentResponse, AppointmentStatus } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import { useIsStaff } from '../../store/session'
import AppointmentActions from './AppointmentActions'
import AppointmentExtraButtons from './AppointmentExtraButtons'
import AppointmentExtraPanel from './AppointmentExtraPanel'
import PaymentPanel from './PaymentPanel'

// El tono de la etiqueta sale del estado, y el estado viene del contrato: si
// el backend agrega uno nuevo, este mapa deja de compilar.
const TONO: Record<AppointmentStatus, string> = {
  pending: 'pending',
  confirmed: 'confirmed',
  completed: 'completed',
  cancelled: 'cancelled',
  no_show: 'cancelled',
}

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

type Extra = 'none' | 'review' | 'complaint' | 'hospitalization'

interface AppointmentRowProps {
  readonly cita: AppointmentResponse
}

export default function AppointmentRow({ cita }: AppointmentRowProps) {
  const [expandido, setExpandido] = useState(false)
  const [extra, setExtra] = useState<Extra>('none')
  const esStaff = useIsStaff()
  const puedeResenar = !esStaff && cita.status === 'completed'
  const puedeInternar = esStaff && cita.status === 'completed'

  const alternar = (valor: Extra) => {
    setExtra(extra === valor ? 'none' : valor)
  }

  return (
    <Fragment>
      <tr>
        <td>{FORMATO.format(new Date(cita.scheduled_at))}</td>
        <td>{cita.duration_minutes} min</td>
        <td>
          <StatusBadge label={cita.status_label} tone={TONO[cita.status]} />
          {cita.cancellation_reason ? <p className="muted">{cita.cancellation_reason}</p> : null}
        </td>
        <td>{cita.description}</td>
        <td className="row-actions">
          <AppointmentActions appointment={cita} />
          <button
            type="button"
            className="btn btn-plain"
            onClick={() => {
              setExpandido(!expandido)
            }}
          >
            {expandido ? 'Ocultar pago' : 'Ver pago'}
          </button>
          <AppointmentExtraButtons
            extra={extra}
            esStaff={esStaff}
            puedeResenar={puedeResenar}
            puedeInternar={puedeInternar}
            onAlternar={alternar}
          />
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={5}>
            <PaymentPanel appointmentId={cita.id} appointmentStatus={cita.status} />
          </td>
        </tr>
      ) : null}
      {extra === 'none' ? null : (
        <tr>
          <td colSpan={5}>
            <AppointmentExtraPanel
              extra={extra}
              appointmentId={cita.id}
              veterinarianId={cita.veterinarian_id}
            />
          </td>
        </tr>
      )}
    </Fragment>
  )
}
