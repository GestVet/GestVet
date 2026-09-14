import HospitalizationDischargeForm from './HospitalizationDischargeForm'
import HospitalizationNoteForm from './HospitalizationNoteForm'

interface HospitalizationManageFormProps {
  readonly hospitalizationId: number
  readonly petId: number
}

/** Notas de seguimiento y alta de una internación abierta. Solo lo ve el personal. */
export default function HospitalizationManageForm({
  hospitalizationId,
  petId,
}: HospitalizationManageFormProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <HospitalizationNoteForm hospitalizationId={hospitalizationId} petId={petId} />
      <HospitalizationDischargeForm hospitalizationId={hospitalizationId} petId={petId} />
    </div>
  )
}
