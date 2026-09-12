import { useClinicalHistoryReport } from '../hooks/useClinicalHistoryReport'
import FormMessage from './FormMessage'
import Icon from './Icon'
import { Button } from './ui/button'

interface ClinicalHistoryReportButtonProps {
  readonly petId: number
}

export default function ClinicalHistoryReportButton({
  petId,
}: ClinicalHistoryReportButtonProps) {
  const reporte = useClinicalHistoryReport(petId)

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        type="button"
        variant="outline"
        disabled={reporte.isPending}
        onClick={() => {
          reporte.mutate()
        }}
      >
        <Icon name="descargar" size={16} />
        <span>{reporte.isPending ? 'Generando PDF…' : 'Descargar historia clínica (PDF)'}</span>
      </Button>
      {reporte.isError ? <FormMessage tone="error">{reporte.errorMessage}</FormMessage> : null}
    </div>
  )
}
