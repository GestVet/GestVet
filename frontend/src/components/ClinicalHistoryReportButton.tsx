import { useClinicalHistoryReport } from '../hooks/useClinicalHistoryReport'
import FormMessage from './FormMessage'
import Icon from './Icon'

interface ClinicalHistoryReportButtonProps {
  readonly petId: number
}

export default function ClinicalHistoryReportButton({
  petId,
}: ClinicalHistoryReportButtonProps) {
  const reporte = useClinicalHistoryReport(petId)

  return (
    <div className="stack">
      <button
        type="button"
        className="btn btn-plain"
        style={{ width: 'fit-content' }}
        disabled={reporte.isPending}
        onClick={() => {
          reporte.mutate()
        }}
      >
        <Icon name="descargar" size={16} />
        <span>{reporte.isPending ? 'Generando PDF…' : 'Descargar historia clínica (PDF)'}</span>
      </button>
      {reporte.isError ? <FormMessage tone="error">{reporte.errorMessage}</FormMessage> : null}
    </div>
  )
}
