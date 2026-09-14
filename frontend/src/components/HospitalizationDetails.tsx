import HospitalizationManageForm from './HospitalizationManageForm'
import HospitalizationNotesList from './HospitalizationNotesList'

interface NoteLike {
  readonly id: number
  readonly note: string
  readonly created_at: string
}

interface HospitalizationLike {
  readonly id: number
  readonly status: string
  readonly discharge_notes: string
  readonly notes: readonly NoteLike[]
}

interface HospitalizationDetailsProps {
  readonly internacion: HospitalizationLike
  readonly petId: number
  readonly canManage: boolean
}

/**
 * El detalle de una internación: sus notas y, si sigue abierta y quien mira
 * es personal, el formulario de seguimiento y alta.
 */
export default function HospitalizationDetails({
  internacion,
  petId,
  canManage,
}: HospitalizationDetailsProps) {
  const abierta = internacion.status === 'open'

  return (
    <div className="flex flex-col gap-4">
      <HospitalizationNotesList notes={internacion.notes} />
      {internacion.discharge_notes ? (
        <p className="m-0 text-sm">
          <strong>Notas de alta:</strong> {internacion.discharge_notes}
        </p>
      ) : null}
      {canManage && abierta ? (
        <HospitalizationManageForm hospitalizationId={internacion.id} petId={petId} />
      ) : null}
    </div>
  )
}
