import { useVaccinationCardPdf } from '../hooks/useVaccinationCardPdf'
import FormMessage from './FormMessage'
import Icon from './Icon'
import { Button } from './ui/button'

interface VaccinationCardPdfButtonProps {
  readonly petId: number
}

/** Baja el carnet para imprimirlo o mandarlo; trae un QR para verificarlo. */
export default function VaccinationCardPdfButton({ petId }: VaccinationCardPdfButtonProps) {
  const carnet = useVaccinationCardPdf(petId)

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={carnet.isPending}
        onClick={() => {
          carnet.mutate()
        }}
      >
        <Icon name="descargar" size={14} />
        <span>{carnet.isPending ? 'Generando…' : 'Descargar carnet (PDF)'}</span>
      </Button>
      {carnet.isError ? <FormMessage tone="error">{carnet.errorMessage}</FormMessage> : null}
    </div>
  )
}
