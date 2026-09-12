import { Fragment, useState } from 'react'

import HospitalizationManageForm from './HospitalizationManageForm'
import HospitalizationNotesList from './HospitalizationNotesList'
import StatusBadge from './StatusBadge'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface NoteLike {
  readonly id: number
  readonly note: string
  readonly created_at: string
}

interface HospitalizationLike {
  readonly id: number
  readonly reason: string
  readonly status: string
  readonly status_label: string
  readonly discharge_notes: string
  readonly admitted_at: string
  readonly discharged_at: string | null
  readonly notes: readonly NoteLike[]
}

interface HospitalizationRowProps {
  readonly internacion: HospitalizationLike
  readonly petId: number
  readonly canManage: boolean
}

/**
 * Una internación, con sus notas de seguimiento.
 *
 * Puramente presentacional salvo por las mutaciones de `HospitalizationManageForm`,
 * que llegan resueltas desde `hooks/useHospitalizations`: así lo puede usar tanto la
 * vista del cliente (`canManage=false`, solo lectura) como la del personal.
 */
export default function HospitalizationRow({
  internacion,
  petId,
  canManage,
}: HospitalizationRowProps) {
  const [expandido, setExpandido] = useState(false)
  const abierta = internacion.status === 'open'

  return (
    <Fragment>
      <tr>
        <td>{FORMATO.format(new Date(internacion.admitted_at))}</td>
        <td>{internacion.reason}</td>
        <td>
          <StatusBadge label={internacion.status_label} tone={abierta ? 'pending' : 'completed'} />
        </td>
        <td>
          {internacion.discharged_at ? FORMATO.format(new Date(internacion.discharged_at)) : '—'}
        </td>
        <td>
          <button
            type="button"
            className="btn btn-plain"
            onClick={() => {
              setExpandido(!expandido)
            }}
          >
            {expandido ? 'Ocultar notas' : `Ver notas (${String(internacion.notes.length)})`}
          </button>
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={5}>
            <div className="stack">
              <HospitalizationNotesList notes={internacion.notes} />
              {internacion.discharge_notes ? (
                <p>
                  <strong>Notas de alta:</strong> {internacion.discharge_notes}
                </p>
              ) : null}
              {canManage && abierta ? (
                <HospitalizationManageForm hospitalizationId={internacion.id} petId={petId} />
              ) : null}
            </div>
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
