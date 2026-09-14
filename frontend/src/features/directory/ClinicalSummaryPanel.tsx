import { useMutation } from '@tanstack/react-query'

import { summarizeClinicalHistory } from '../../api/medicalRecords'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionHeading from '../../components/SectionHeading'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'
import ClinicalSummaryResult from './ClinicalSummaryResult'

interface ClinicalSummaryPanelProps {
  readonly petId: number
}

/**
 * Resumen de la historia con IA, para preparar la consulta.
 *
 * Se pide a mano y no al abrir la ficha: cada resumen cuesta y no siempre hace
 * falta. El resultado vive solo en pantalla; no se guarda en la historia.
 */
export default function ClinicalSummaryPanel({ petId }: ClinicalSummaryPanelProps) {
  const resumen = useMutation({ mutationFn: () => summarizeClinicalHistory(petId) })
  let etiqueta = 'Resumir historia'
  if (resumen.isPending) {
    etiqueta = 'Resumiendo…'
  } else if (resumen.isSuccess) {
    etiqueta = 'Volver a resumir'
  }

  return (
    <section className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-4" aria-busy={resumen.isPending}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionHeading as="h3" description="Ficha, vacunas e historia resumidas por IA antes de la consulta.">
          Resumen con IA
        </SectionHeading>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={resumen.isPending}
          onClick={() => {
            resumen.mutate()
          }}
        >
          <Icon name="ia" size={14} />
          <span>{etiqueta}</span>
        </Button>
      </div>
      <div aria-live="polite" className="flex flex-col gap-4">
        {resumen.isError ? (
          <FormMessage tone="error">
            {errorMessage(resumen.error, 'No se pudo generar el resumen.')}
          </FormMessage>
        ) : null}
        {resumen.data === undefined ? null : <ClinicalSummaryResult resultado={resumen.data} />}
      </div>
    </section>
  )
}
